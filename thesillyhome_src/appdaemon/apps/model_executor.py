# Library imports
import string
import appdaemon.plugins.hass.hassapi as hass
import pickle
import pandas as pd
import copy
import os.path
import logging
import datetime
import sqlite3 as sql
import pytz
import numpy as np
import time
import json
from collections import deque

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    def initialize(self):
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
        self.automation_triggered = set()  # Track which entities were triggered by automation
        self.switch_logs = {}  # Track recent switch times for each actuator
        self.blocked_actuators = {}  # Track blocked actuators with unblocking times
        self.init_db()
        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome Model Executor fully initialized!")

    def read_actuators(self):
        enabled_actuators = set()
        with open(
            "/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r"
        ) as f:
            metrics_data = json.load(f)
        for metric in metrics_data:
            if metric["model_enabled"]:
                enabled_actuators.add(metric["actuator"])
        self.log(f"Enabled Actuators: {enabled_actuators}")
        return enabled_actuators

    def init_db(self):
        with sql.connect(self.states_db) as con:
            feature_list = self.get_base_columns()
            feature_list = self.unverified_features(feature_list)
            db_rules_engine = pd.DataFrame(columns=feature_list)
            db_rules_engine.loc[0] = 1
            db_rules_engine["entity_id"] = "dummy"
            db_rules_engine["state"] = 1

            self.log(f"Initialized rules engine DB", level="INFO")
            try:
                db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace")
            except:
                self.log(f"DB already exists. Skipping", level="INFO")

    def unverified_features(self, feature_list):
        feature_list = self.get_new_feature_list(feature_list, "hour_")
        feature_list = self.get_new_feature_list(feature_list, "last_state_")
        feature_list = self.get_new_feature_list(feature_list, "weekday_")
        feature_list = self.get_new_feature_list(feature_list, "switch")

        return feature_list

    def log_automatic_action(self, act, action):
        self.track_switch(act)
        if self.is_blocked(act):
            self.log(f"Automatische Aktion blockiert: {act} wurde nicht {action} (zu viele Schaltvorgänge).", level="WARNING")
            return
        self.log(f"Automatisch: {act} wurde {action}.", level="INFO")

    def log_manual_action(self, act, state):
        now = datetime.datetime.now()

        if act in self.switch_logs:
            recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 60]
            if recent_switches:
                self.blocked_actuators[act] = now + datetime.timedelta(seconds=300)
                self.log(f"Manuell: {act} wurde geändert auf {state}. Automatische Aktion in den letzten 60 Sekunden erkannt. {act} ist jetzt für 300 Sekunden blockiert.", level="WARNING")
                return

        self.log(f"Manuell: {act} wurde geändert auf {state}.", level="INFO")
        self.blocked_actuators[act] = now + datetime.timedelta(seconds=600)

    def is_blocked(self, act):
        if act in self.blocked_actuators:
            unblock_time = self.blocked_actuators[act]
            if datetime.datetime.now() < unblock_time:
                self.log(f"{act} is currently blocked until {unblock_time}.", level="WARNING")
                return True
            else:
                del self.blocked_actuators[act]
        return False

    def track_switch(self, act):
        now = datetime.datetime.now()
        if act not in self.switch_logs:
            self.switch_logs[act] = deque(maxlen=10)
        self.switch_logs[act].append(now)

        recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 30]
        if len(recent_switches) > 6:
            self.blocked_actuators[act] = now + datetime.timedelta(seconds=900)
            self.log(f"{act} has been blocked for 900 seconds due to excessive switching.", level="ERROR")

    def verify_rules(
        self,
        act: string,
        rules_to_verify: pd.DataFrame,
        prediction: int,
        all_rules: pd.DataFrame,
    ):
        self.log("Executing: verify_rules")

        t = time.process_time()
        all_rules = all_rules[all_rules["entity_id"] == act]

        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify)
            assert len(matching_rule) in [
                0,
                1,
                2,
            ], "        More than 2 matching rules.  Please reach out in https://discord.gg/bCM2mX9S for assistance."
            rules_state = matching_rule["state"].values

            if len(matching_rule) == 2:
                self.log(f"--- These set of features are ambigious. Do nothing.")
                elapsed_time = time.process_time() - t
                self.log(f"---verify_rules took: {elapsed_time}")
                return False

            elif (len(matching_rule) == 1) and (rules_state != prediction):
                self.log(
                    f"--- This will not be executed as it is part of the excluded rules."
                )
                elapsed_time = time.process_time() - t
                self.log(f"---verify_rules took: {elapsed_time}")
                return False
            else:
                elapsed_time = time.process_time() - t
                self.log(f"---verify_rules took: {elapsed_time}")
                self.log("      No matching rules")
                return True
        else:
            elapsed_time = time.process_time() - t
            self.log(f"---verify_rules took: {elapsed_time}")
            self.log(f"--- No matching rules, empty DB for {act}")
            return True

    def add_rules(
        self,
        training_time: datetime.datetime,
        actuator: string,
        new_state: int,
        new_rule: pd.DataFrame,
        all_rules: pd.DataFrame,
    ):
        self.log("Executing: add_rules")
        t = time.process_time()

        utc = pytz.UTC
        last_states = self.last_states

        last_states_tmp = last_states.copy()
        current_states_tmp = self.get_state()
        last_states_tmp = {
            your_key: last_states_tmp[your_key] for your_key in tsh_config.devices
        }
        current_states_tmp = {
            your_key: current_states_tmp[your_key] for your_key in tsh_config.devices
        }
        del last_states_tmp[actuator]
        del current_states_tmp[actuator]

        states_no_change = last_states_tmp == current_states_tmp

        last_update_time = datetime.datetime.strptime(
            last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        now_minus_training_time = utc.localize(
            datetime.datetime.now() - datetime.timedelta(seconds=training_time)
        )
        self.log(
            f"---states_no_change: {states_no_change}, last_state: {last_states[actuator]['state']} new_state: {new_state}"
        )
        self.log(
            f"---last_update_time: {(utc.localize(datetime.datetime.now()) - last_update_time)}"
        )

        if (
            states_no_change
            and last_states[actuator]["state"] != new_state
            and last_update_time > now_minus_training_time
        ):
            new_rule["state"] = np.where(new_rule["state"] == "on", 1, 0)
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()

            if not new_all_rules.equals(all_rules):
                self.log(f"---Adding new rule for {actuator}")

                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")
            else:
                self.log(f"---Rule already exists for {actuator}")
        else:
            elapsed_time = time.process_time() - t
            self.log(f"---add_rules {elapsed_time}")

    def load_models(self):
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            if os.path.isfile(f"{tsh_config.data_dir}/model/{act}/best_model.pkl"):
                with open(
                    f"{tsh_config.data_dir}/model/{act}/best_model.pkl",
                    "rb",
                ) as pickle_file:
                    content = pickle.load(pickle_file)
                    act_model_set[act] = content
            else:
                logging.info(f"No model for {act}")
        return act_model_set

    def get_base_columns(self):
        base_columns = pd.read_pickle(
            f"{tsh_config.data_dir}/parsed/act_states.pkl"
        ).columns
        base_columns = sorted(
            list(set(base_columns) - set(["entity_id", "state", "duplicate"]))
        )
        return base_columns

    def get_new_feature_list(self, feature_list: list, device: string):
        cur_list = []
        for feature in feature_list:
            if feature.startswith(device):
                cur_list.append(feature)
        new_feature_list = sorted(list(set(feature_list) - set(cur_list)))
        return new_feature_list

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        float_sensors = tsh_config.float_sensors
        devices = tsh_config.devices
        now = datetime.datetime.now()

        if entity in devices:
            self.log(f"\n")
            self.log(f"<--- {entity} is {new} --->")

            feature_list = self.get_base_columns()

            current_state_base = pd.DataFrame(columns=feature_list)
            current_state_base.loc[0] = 0

            df_sen_states = copy.deepcopy(current_state_base)
            for sensor in sensors:
                true_state = self.get_state(entity_id=sensor)
                if sensor not in float_sensors:
                    if f"{sensor}_{true_state}" in df_sen_states.columns:
                        df_sen_states[sensor + "_" + true_state] = 1
                elif sensor in float_sensors:
                    if (true_state) in df_sen_states.columns:
                        df_sen_states[sensor] = true_state

            last_states = self.last_states
            all_states = self.get_state()

            df_sen_states[f"hour_{now.hour}"] = 1
            df_sen_states[f"weekday_{now.weekday()}"] = 1

            with sql.connect(self.states_db) as con:
                all_rules = pd.read_sql(
                    f"SELECT * FROM rules_engine",
                    con=con,
                )
                all_rules = all_rules.drop(columns=["index"])

            enabled_actuators = self.read_actuators()

            if entity in sensors:
                for act, model in self.act_model_set.items():
                    self.log(f"Prediction sequence for: {act}")

                    df_sen_states_less = df_sen_states[
                        self.get_new_feature_list(feature_list, act)
                    ]

                    prediction = model.predict(df_sen_states_less)

                    rule_to_verify = df_sen_states_less.copy()
                    rule_to_verify = rule_to_verify[
                        self.unverified_features(
                            rule_to_verify.columns.values.tolist()
                        )
                    ]
                    rule_to_verify["entity_id"] = act

                    if self.verify_rules(
                        act, rule_to_verify, prediction, all_rules
                    ):
                        self.log(
                            f"---Predicted {act} as {prediction}", level="INFO"
                        )

                        if act in enabled_actuators:
                            if (prediction == 1) and (all_states[act]["state"] != "on"):
                                if not self.is_blocked(act):
                                    self.log(f"---Turn on {act}")
                                    self.turn_on(act)
                                    self.track_switch(act)
                                    self.automation_triggered.add(act)
                                    self.log_automatic_action(act, "eingeschaltet")
                                else:
                                    self.log(f"---{act} is blocked, skipping action.")

                            elif (prediction == 0) and (
                                all_states[act]["state"] != "off"
                            ):
                                if not self.is_blocked(act):
                                    self.log(f"---Turn off {act}")
                                    self.turn_off(act)
                                    self.track_switch(act)
                                    self.automation_triggered.add(act)
                                    self.log_automatic_action(act, "ausgeschaltet")
                                else:
                                    self.log(f"---{act} is blocked, skipping action.")

                        else:
                            current_state = all_states[act]["state"]
                            correct_prediction = (
                                (prediction == 1 and current_state == "on") or
                                (prediction == 0 and current_state == "off")
                            )
                            if correct_prediction:
                                self.log(f"---Prediction for {act} was correct.", level="INFO")
                            else:
                                self.log(f"---Prediction for {act} was incorrect.", level="WARNING")

            for act in actuators:
                current_state = all_states[act]["state"]

                if act not in self.last_states or self.last_states[act]["state"] != current_state:
                    if act in self.automation_triggered:
                        self.automation_triggered.remove(act)
                    else:
                        self.log_manual_action(act, current_state)

            self.last_states = self.get_state()
