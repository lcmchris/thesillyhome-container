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

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config


class ModelExecutor(hass.Hass):
    def initialize(self):
        # Define columns for current_state_base DataFrame
        feature_list = self.get_base_columns()
        current_state_base = pd.DataFrame(columns=feature_list)
        # Set initial values in current_state_base DataFrame
        current_state_base.loc[0] = 0
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
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
        """
        Initialize db with all potential hot encoded features.
        """
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
        """
        There are features that shouldn't be verified. hour_, weekday_, last_state_
        """
        feature_list = self.get_new_feature_list(feature_list, "hour_")
        feature_list = self.get_new_feature_list(feature_list, "last_state_")
        feature_list = self.get_new_feature_list(feature_list, "weekday_")
        feature_list = self.get_new_feature_list(feature_list, "switch")

        return feature_list

    def verify_rules(
        self,
        act: string,
        rules_to_verify: pd.DataFrame,
        prediction: int,
        all_rules: pd.DataFrame,
    ):

        """
        Check states when making an action based on prediction.
        For an Actuator, don't execute predction when there is a case
        where the same state is seen in the rules, but the state is different
        """
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
        """
        Add a new rule to the rules engine if:
        1) New Actuator activity occurs
        2) All the states are the same as last states
        3) Time past within training_time.

        Rule will include - states of all entities, except for the actuator - entity_id and state.

        No return
        """
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

        # self.log(last_states_tmp)
        # self.log(current_states_tmp)

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
            self.log(f"---Rules not added")

    def load_models(self):
        """
        Loads all models to a dictionary
        """
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
        # Get feature list from parsed data header, set all columns to 0
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

            # Get feature list from parsed data header, set all columns to 0
            feature_list = self.get_base_columns()

            current_state_base = pd.DataFrame(columns=feature_list)
            current_state_base.loc[0] = 0

            # Get current state of all sensors for model input
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

            # Extract current date
            # datetime object containing current date and time
            # dd/mm/YY H:M:S
            df_sen_states[f"hour_{now.hour}"] = 1
            df_sen_states[f"weekday_{now.weekday()}"] = 1
            self.log(
                f"Time is : hour_{now.hour} & weekday_{now.weekday()}", level="DEBUG"
            )

            # Check rules for actuators against rules engine
            with sql.connect(self.states_db) as con:
                all_rules = pd.read_sql(
                    f"SELECT * FROM rules_engine",
                    con=con,
                )
                all_rules = all_rules.drop(columns=["index"])

            enabled_actuators = self.read_actuators()
            if entity in actuators:
                # Adding rules
                new_rule = df_sen_states.copy()
                # Don't check the device's state itself
                new_rule = new_rule[self.get_new_feature_list(feature_list, entity)]
                new_rule = new_rule[
                    self.unverified_features(new_rule.columns.values.tolist())
                ]
                new_rule["entity_id"] = entity
                new_rule["state"] = new
                training_time = 10
                self.add_rules(training_time, entity, new, new_rule, all_rules)

            # Execute all models for sensor and set states
            if entity in sensors:
                for act, model in self.act_model_set.items():
                    if act in enabled_actuators:
                        self.log(f"Prediction sequence for: {act}")

                        # the actuators feature state should not affect the model and also the duplicate column
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
                            # Execute actions
                            self.log(
                                f"---Predicted {act} as {prediction}", level="INFO"
                            )
                            if (prediction == 1) and (all_states[act]["state"] != "on"):
                                self.log(f"---Turn on {act}")
                                self.turn_on(act)
                            elif (prediction == 0) and (
                                all_states[act]["state"] != "off"
                            ):
                                self.log(f"---Turn off {act}")
                                self.turn_off(act)
                            else:
                                self.log(f"---{act} state has not changed.")
                    else:
                        self.log("Ignore Disabled actuator")

            self.last_states = self.get_state()
