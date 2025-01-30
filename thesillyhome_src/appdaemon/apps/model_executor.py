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
import gc
from collections import deque

import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    def initialize(self):
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.automation_triggered = set()
        self.switch_logs = {}
        self.blocked_actuators = {}
        self.init_db()
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
            except Exception:
                self.log(f"DB already exists. Skipping", level="INFO")

    def state_handler(self, entity, attribute, old, new, kwargs):
        if old == new:
            return  # Vermeide doppelte Verarbeitung, wenn sich der Zustand nicht geändert hat

        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        devices = tsh_config.devices
        now = datetime.datetime.now()

        # Aktuelle Datenbankabfrage mit Filterung nach entity_id
        with sql.connect(self.states_db) as con:
            query = f"SELECT * FROM rules_engine WHERE entity_id = '{entity}'"
            all_rules = pd.read_sql(query, con=con).drop(columns=["index"])

        feature_list = self.get_base_columns()

        current_state_base = pd.DataFrame(columns=feature_list)
        current_state_base.loc[0] = 0

        # Aktuelle Sensorzustände sammeln
        df_sen_states = copy.deepcopy(current_state_base)
        for sensor in sensors:
            true_state = self.get_state(entity_id=sensor)
            if f"{sensor}_{true_state}" in df_sen_states.columns:
                df_sen_states[f"{sensor}_{true_state}"] = 1

        enabled_actuators = self.read_actuators()

        if entity in actuators:
            if self.is_blocked(entity):
                return

            # Neue Regel für den aktuellen Zustand hinzufügen
            new_rule = df_sen_states.copy()
            new_rule = new_rule[self.get_new_feature_list(feature_list, entity)]
            new_rule["entity_id"] = entity
            new_rule["state"] = new
            training_time = 20
            self.add_rules(training_time, entity, new, new_rule, all_rules)

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
                        self.log(f"---Predicted {act} as {prediction}", level="INFO")

                        if (prediction == 1) and (self.get_state(entity_id=act)["state"] != "on"):
                            if not self.is_blocked(act):
                                self.log(f"---Turn on {act}")
                                self.turn_on(act)
                                self.track_switch(act)
                                self.automation_triggered.add(act)
                                self.log_automatic_action(act, "eingeschaltet")

                        elif (prediction == 0) and (self.get_state(entity_id=act)["state"] != "off"):
                            if not self.is_blocked(act):
                                self.log(f"---Turn off {act}")
                                self.turn_off(act)
                                self.track_switch(act)
                                self.automation_triggered.add(act)
                                self.log_automatic_action(act, "ausgeschaltet")

        # Speicher freigeben
        del all_rules, df_sen_states
        gc.collect()

    def verify_rules(self, act, rules_to_verify, prediction, all_rules):
        self.log("Executing: verify_rules")
        all_rules = all_rules[all_rules["entity_id"] == act]

        if all_rules.empty:
            self.log(f"--- No matching rules, empty DB for {act}")
            return True

        matching_rule = all_rules.merge(rules_to_verify, how="inner")
        if matching_rule.empty:
            return True

        if len(matching_rule) > 1:
            self.log(f"--- These set of features are ambiguous. Do nothing.")
            return False

        return matching_rule["state"].values[0] == prediction

    def add_rules(self, training_time, actuator, new_state, new_rule, all_rules):
        last_update_time = datetime.datetime.strptime(self.last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z")
        now_minus_training_time = datetime.datetime.now() - datetime.timedelta(seconds=training_time)

        if last_update_time > now_minus_training_time and self.last_states[actuator]["state"] != new_state:
            new_rule["state"] = 1 if new_rule["state"] == "on" else 0
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()

            if not new_all_rules.equals(all_rules):
                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")

    def load_models(self):
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
            if os.path.isfile(model_path):
                with open(model_path, "rb") as pickle_file:
                    act_model_set[act] = pickle.load(pickle_file)
        return act_model_set

    def get_base_columns(self):
        base_columns = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns
        return sorted(list(set(base_columns) - {"entity_id", "state", "duplicate"}))

    def get_new_feature_list(self, feature_list, device):
        return sorted([feature for feature in feature_list if not feature.startswith(device)])

    def is_blocked(self, act):
        return act in self.blocked_actuators and datetime.datetime.now() < self.blocked_actuators[act]

    def track_switch(self, act):
        if act not in self.switch_logs:
            self.switch_logs[act] = deque(maxlen=10)
        self.switch_logs[act].append(datetime.datetime.now())
