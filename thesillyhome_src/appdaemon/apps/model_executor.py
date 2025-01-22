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

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    def initialize(self):
        self.device_states = {}
        self.manual_override = {}
        self.error_log = []

        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
        self.init_db()

        for device in tsh_config.devices:
            self.device_states[device] = {
                "state": "off",
                "changes": 0,
                "last_changed": datetime.datetime.min
            }

        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome Model Executor fully initialized!")

    def read_actuators(self):
        enabled_actuators = set()
        with open("/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r") as f:
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

    def log_error(self, entity, action, reason):
        self.error_log.append({
            "entity": entity,
            "action": action,
            "reason": reason,
            "timestamp": datetime.datetime.now()
        })
        self.log(f"Fehler für {entity}: {reason}")

    def clear_override(self, kwargs):
        entity = kwargs["entity"]
        self.manual_override[entity] = False
        self.log(f"---Manuelle Sperre für {entity} aufgehoben.")

    def verify_rules(self, act, rules_to_verify, prediction, all_rules):
        relevant_rules = all_rules[(all_rules["entity_id"] == act) & (all_rules["state"] != prediction)]

        if not relevant_rules.empty:
            self.log_error(act, "rule_violation", "Regel verhindert Aktion")
            return False

        return True

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        float_sensors = tsh_config.float_sensors
        devices = tsh_config.devices
        now = datetime.datetime.now()

        if entity in devices:
            self.log(f"\n")
            self.log(f"<--- {entity} is {new} --->")

            if entity in actuators:
                device_state = self.device_states[entity]

                if device_state["state"] == "on" and new == "off" and device_state["changes"] >= 2:
                    self.log(f"---Maximale Ausschaltversuche für {entity} erreicht. Ignoriere.")
                    return

                if self.manual_override.get(entity, False):
                    self.log(f"---{entity} ist manuell gesperrt. Automatische Aktion ignoriert.")
                    return

                if old != new and not self.manual_override.get(entity, False):
                    self.manual_override[entity] = True
                    self.run_in(self.clear_override, 90, entity=entity)

                    device_state["state"] = new
                    if new != old:
                        device_state["changes"] += 1
                        device_state["last_changed"] = datetime.datetime.now()

                self.device_states[entity] = device_state

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

            df_sen_states[f"hour_{now.hour}"] = 1
            df_sen_states[f"weekday_{now.weekday()}"] = 1
            self.log(f"Time is : hour_{now.hour} & weekday_{now.weekday()}", level="DEBUG")

            with sql.connect(self.states_db) as con:
                all_rules = pd.read_sql(f"SELECT * FROM rules_engine", con=con).drop(columns=["index"])

            enabled_actuators = self.read_actuators()
            if entity in sensors:
                for act, model in self.act_model_set.items():
                    if act in enabled_actuators:
                        self.log(f"Prediction sequence for: {act}")

                        df_sen_states_less = df_sen_states[self.get_new_feature_list(feature_list, act)]
                        prediction = model.predict(df_sen_states_less)

                        rule_to_verify = df_sen_states_less.copy()
                        rule_to_verify = rule_to_verify[self.unverified_features(rule_to_verify.columns.values.tolist())]
                        rule_to_verify["entity_id"] = act

                        if self.verify_rules(act, rule_to_verify, prediction, all_rules):
                            if (prediction == 1) and (self.get_state(act) != "on") and not self.manual_override.get(act, False):
                                self.log(f"---Turn on {act}")
                                self.turn_on(act)
                            elif (prediction == 0) and (self.get_state(act) != "off") and not self.manual_override.get(act, False):
                                self.log(f"---Turn off {act}")
                                self.turn_off(act)
                            else:
                                self.log(f"---{act} state has not changed.")

    def add_rules(self, training_time, actuator, new_state, new_rule, all_rules):
        self.log("Executing: add_rules")
        t = time.process_time()

        utc = pytz.UTC
        last_states = self.last_states

        last_states_tmp = last_states.copy()
        current_states_tmp = self.get_state()
        last_states_tmp = {key: last_states_tmp[key] for key in tsh_config.devices}
        current_states_tmp = {key: current_states_tmp[key] for key in tsh_config.devices}
        del last_states_tmp[actuator]
        del current_states_tmp[actuator]

        states_no_change = last_states_tmp == current_states_tmp

        last_update_time = datetime.datetime.strptime(last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z")
        now_minus_training_time = utc.localize(datetime.datetime.now() - datetime.timedelta(seconds=training_time))

        if states_no_change and last_states[actuator]["state"] != new_state and last_update_time > now_minus_training_time:
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
            self.log(f"---Rules not added")

    def load_models(self):
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            if os.path.isfile(f"{tsh_config.data_dir}/model/{act}/best_model.pkl"):
                with open(f"{tsh_config.data_dir}/model/{act}/best_model.pkl", "rb") as pickle_file:
                    content = pickle.load(pickle_file)
                    content.probability_threshold = 0.6
                    act_model_set[act] = content
            else:
                logging.info(f"No model for {act}")
        return act_model_set

    def get_base_columns(self):
        base_columns = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns
        base_columns = sorted(list(set(base_columns) - set(["entity_id", "state", "duplicate"])))
        return base_columns

    def get_new_feature_list(self, feature_list, device):
        cur_list = [feature for feature in feature_list if feature.startswith(device)]
        new_feature_list = sorted(list(set(feature_list) - set(cur_list)))
        return new_feature_list
