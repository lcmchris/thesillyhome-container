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
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
        self.manual_override = {}
        self.action_counters = {}
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
        Added rules for manual override priority and action frequency.
        """
        self.log("Executing: verify_rules")

        t = time.process_time()
        all_rules = all_rules[all_rules["entity_id"] == act]

        if act in self.manual_override:
            override_time = self.manual_override[act]
            if (datetime.datetime.now() - override_time).total_seconds() < 90:
                self.log(f"Manual override active for {act}. Skipping execution.")
                return False

        if act in self.action_counters:
            action_times = self.action_counters[act]
            recent_actions = [
                at for at in action_times if (datetime.datetime.now() - at).total_seconds() <= 30
            ]
            if len(recent_actions) >= 2:
                self.log(f"{act} toggled more than twice in 30 seconds. Skipping execution.")
                return False

        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify)
            assert len(matching_rule) in [
                0,
                1,
                2,
            ], "More than 2 matching rules. Please reach out for assistance."
            rules_state = matching_rule["state"].values

            if len(matching_rule) == 2:
                self.log(f"--- These set of features are ambiguous. Do nothing.")
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

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        devices = tsh_config.devices
        now = datetime.datetime.now()

        if entity in devices:
            self.log(f"\n")
            self.log(f"<--- {entity} is {new} --->")

            if entity in actuators:
                if old != new:
                    self.manual_override[entity] = now
                    self.log(f"Manual override detected for {entity}. Suppressing KI for 90 seconds.")

                    if entity not in self.action_counters:
                        self.action_counters[entity] = []
                    self.action_counters[entity].append(now)

            enabled_actuators = self.read_actuators()
            if entity in sensors:
                for act, model in self.act_model_set.items():
                    if act in enabled_actuators:
                        self.log(f"Prediction sequence for: {act}")
                        df_sen_states = self.get_sensor_states(entity, sensors)
                        prediction = model.predict(df_sen_states)
                        if self.verify_rules(act, df_sen_states, prediction, all_rules):
                            self.execute_action(act, prediction)

    def execute_action(self, act, prediction):
        all_states = self.get_state()
        if prediction == 1 and all_states[act]["state"] != "on":
            self.log(f"---Turn on {act}")
            self.turn_on(act)
        elif prediction == 0 and all_states[act]["state"] != "off":
            self.log(f"---Turn off {act}")
            self.turn_off(act)
        else:
            self.log(f"---{act} state has not changed.")
