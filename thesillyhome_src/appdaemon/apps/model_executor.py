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

    def create_rule_from_state(self, current_states):
        """
        Erstellt eine neue Regel auf Basis der aktuellen Sensorzustände.
        """
        feature_list = self.get_base_columns()
        rule_data = pd.DataFrame(columns=feature_list)
        rule_data.loc[0] = 0  # Alle Werte initialisieren

        # Zustände verarbeiten und in Regel einfügen
        for entity, value in current_states.items():
            if f"{entity}_{value}" in rule_data.columns:
                rule_data.at[0, f"{entity}_{value}"] = 1

        # Zeitmerkmale hinzufügen
        now = datetime.datetime.now()
        rule_data[f"hour_{now.hour}"] = 1
        rule_data[f"weekday_{now.weekday()}"] = 1

        return rule_data

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
        Filter out features that should not be verified.
        """
        feature_list = self.get_new_feature_list(feature_list, "hour_")
        feature_list = self.get_new_feature_list(feature_list, "last_state_")
        feature_list = self.get_new_feature_list(feature_list, "weekday_")
        feature_list = self.get_new_feature_list(feature_list, "switch")
        return feature_list

    def log_automatic_action(self, act, action):
        """
        Logs an action that was triggered automatically.
        Adds flipping detection to prevent excessive toggling.
        """
        self.track_switch(act)
        if self.is_blocked(act):
            self.log(f"Automatische Aktion blockiert: {act} wurde nicht {action} (zu viele Schaltvorgänge).", level="WARNING")
            return
        self.log(f"Automatisch: {act} wurde {action}.", level="INFO")

    def log_manual_action(self, act, state):
        """
        Logs an action that was triggered manually.
        If the actuator was automatically triggered in the last 60 seconds,
        it blocks the actuator for 300 seconds.
        """
        now = datetime.datetime.now()

        # Erstelle neue Regel basierend auf aktuellen Zuständen
        current_states = self.get_state()
        new_rule = self.create_rule_from_state(current_states)
        new_rule["entity_id"] = act
        new_rule["state"] = 1 if state == "on" else 0

        # Regel speichern
        with sql.connect(self.states_db) as con:
            new_rule.to_sql("rules_engine", con=con, if_exists="append")

        # Überprüfung auf automatische Auslösung in den letzten 90 Sekunden
        if act in self.switch_logs:
            recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 90]
            if recent_switches:
                self.blocked_actuators[act] = now + datetime.timedelta(seconds=1800)
                self.log(f"Manuell: {act} wurde geändert auf {state}. Automatische Aktion erkannt. {act} für 1800 Sekunden blockiert.", level="WARNING")
                return

        self.log(f"Manuell: {act} wurde geändert auf {state}.", level="INFO")
        self.blocked_actuators[act] = now + datetime.timedelta(seconds=900)

    def is_blocked(self, act):
        if act in self.blocked_actuators:
            unblock_time = self.blocked_actuators[act]
            if datetime.datetime.now() < unblock_time:
                self.log(f"{act} is currently blocked until {unblock_time}.", level="WARNING")
                return True
            else:
                del self.blocked_actuators[act]  # Unblock the actuator
        return False

    def track_switch(self, act):
        now = datetime.datetime.now()
        if act not in self.switch_logs:
            self.switch_logs[act] = deque(maxlen=10)
        self.switch_logs[act].append(now)

        recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 30]
        if len(recent_switches) > 6:
            self.blocked_actuators[act] = now + datetime.timedelta(seconds=1800)
            self.log(f"{act} has been blocked for 1800 seconds due to excessive switching.", level="ERROR")

    def verify_rules(self, act, rules_to_verify, prediction, all_rules):
        self.log("Executing: verify_rules")
        all_rules = all_rules[all_rules["entity_id"] == act]

        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify)
            if len(matching_rule) == 2:
                self.log(f"--- These set of features are ambiguous. Do nothing.")
                return False
            elif (len(matching_rule) == 1) and (matching_rule["state"].values[0] != prediction):
                self.log(f"--- This will not be executed as it is part of the excluded rules.")
                return False
        else:
            self.log(f"--- No matching rules, empty DB for {act}")
            return True

        self.log("No matching rules found. Proceeding with prediction.")
        return True

    def add_rules(self, training_time, actuator, new_state, new_rule, all_rules):
        self.log("Executing: add_rules")

        last_update_time = datetime.datetime.strptime(
            self.last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        if (self.last_states[actuator]["state"] != new_state) and \
           (datetime.datetime.now() - last_update_time).total_seconds() > training_time:
            new_rule["state"] = new_state
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()
            if not new_all_rules.equals(all_rules):
                self.log(f"---Adding new rule for {actuator}")
                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")
            else:
                self.log(f"---Rule already exists for {actuator}")

    def load_models(self):
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            if os.path.isfile(f"{tsh_config.data_dir}/model/{act}/best_model.pkl"):
                with open(f"{tsh_config.data_dir}/model/{act}/best_model.pkl", "rb") as file:
                    act_model_set[act] = pickle.load(file)
            else:
                logging.info(f"No model for {act}")
        return act_model_set

    def get_base_columns(self):
        return pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns

    def get_new_feature_list(self, feature_list, device):
        return sorted([feature for feature in feature_list if not feature.startswith(device)])

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        now = datetime.datetime.now()

        if entity in sensors:
            self.log(f"Handling state change for: {entity}")
            df_sen_states = self.create_rule_from_state(self.get_state())

            for act, model in self.act_model_set.items():
                if act in self.read_actuators():
                    prediction = model.predict(df_sen_states)
                    self.log(f"Predicted {act} as {prediction}")
                    if self.verify_rules(act, df_sen_states, prediction, pd.DataFrame()):
                        self.turn_on(act) if prediction == 1 else self.turn_off(act)
