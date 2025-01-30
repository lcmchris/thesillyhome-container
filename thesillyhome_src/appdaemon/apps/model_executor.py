import string
import appdaemon.plugins.hass.hassapi as hass
import pickle
import pandas as pd
import copy
import os
import logging
import datetime
import sqlite3 as sql
import pytz
import numpy as np
import json
from collections import deque

# Import der Konfiguration
import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    
    # Konstante für die Datenpfade
    METRICS_MATRIX_PATH = "/thesillyhome_src/frontend/static/data/metrics_matrix.json"
    STATES_DB_PATH = "/thesillyhome_src/appdaemon/apps/tsh.db"
    
    def initialize(self):
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.last_states = self.get_state()
        self.switch_logs = {}
        self.blocked_actuators = {}
        self.init_db()
        self.log_info("TheSillyHome Model Executor initialized")

    # --- Utility Funktionen ---
    
    def log_info(self, message):
        self.log(message, level="INFO")

    def log_warning(self, message):
        self.log(message, level="WARNING")

    def log_error(self, message):
        self.log(message, level="ERROR")

    def get_rules_from_db(self):
        with sql.connect(self.STATES_DB_PATH) as con:
            return pd.read_sql("SELECT * FROM rules_engine", con)

    def get_enabled_actuators(self):
        try:
            with open(self.METRICS_MATRIX_PATH, "r") as f:
                metrics_data = json.load(f)
            return {metric["actuator"] for metric in metrics_data if metric.get("model_enabled")}
        except Exception as e:
            self.log_warning(f"Fehler beim Lesen der metrics_matrix.json: {e}")
            return set()

    def create_rule_from_state(self, current_states):
        feature_list = self.get_base_columns()
        rule_data = pd.DataFrame(columns=feature_list)
        rule_data.loc[0] = 0

        for entity, value in current_states.items():
            if f"{entity}_{value}" in rule_data.columns:
                rule_data.at[0, f"{entity}_{value}"] = 1

        now = datetime.datetime.now()
        rule_data[f"hour_{now.hour}"] = 1
        rule_data[f"weekday_{now.weekday()}"] = 1

        return rule_data

    def get_base_columns(self):
        return pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns

    # --- Modell Laden ---
    
    def load_models(self):
        actuators = tsh_config.actuators
        models = {}
        for act in actuators:
            model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
            if os.path.isfile(model_path):
                with open(model_path, "rb") as file:
                    models[act] = pickle.load(file)
            else:
                self.log_warning(f"Kein Modell für {act} gefunden.")
        return models

    # --- Regelprüfung und Aktionen ---
    
    def verify_rules(self, act, rules_to_verify, prediction, all_rules):
        rules = all_rules[all_rules["entity_id"] == act]

        if not rules.empty:
            matching_rule = rules.merge(rules_to_verify)
            if len(matching_rule) == 2:
                self.log_info(f"Ambiguity detected in rules for {act}. Skipping.")
                return False
            elif len(matching_rule) == 1 and matching_rule["state"].values[0] != prediction:
                self.log_info(f"Excluded rule matched for {act}. Skipping action.")
                return False
        else:
            self.log_info(f"No matching rules found for {act}. Proceeding.")
            return True

        return True

    def handle_action(self, act, prediction):
        if prediction == 1:
            self.turn_on(act)
            self.log_info(f"Aktor {act} eingeschaltet.")
        else:
            self.turn_off(act)
            self.log_info(f"Aktor {act} ausgeschaltet.")

    # --- Lernprozesse und Blockierung ---
    
    def log_manual_action(self, act, state):
        current_states = self.get_state()
        new_rule = self.create_rule_from_state(current_states)
        new_rule["entity_id"] = act
        new_rule["state"] = 1 if state == "on" else 0

        with sql.connect(self.STATES_DB_PATH) as con:
            new_rule.to_sql("rules_engine", con=con, if_exists="append")

        now = datetime.datetime.now()
        if act in self.switch_logs:
            recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 90]
            if recent_switches:
                self.blocked_actuators[act] = now + datetime.timedelta(seconds=1800)
                self.log_warning(f"Aktor {act} wurde blockiert (manuelle Änderung erkannt).")
                return

        self.log_info(f"Manuelle Aktion für {act}: Zustand geändert auf {state}.")
        self.blocked_actuators[act] = now + datetime.timedelta(seconds=900)

    def is_blocked(self, act):
        if act in self.blocked_actuators:
            if datetime.datetime.now() < self.blocked_actuators[act]:
                self.log_warning(f"{act} ist blockiert. Aktion abgebrochen.")
                return True
            else:
                del self.blocked_actuators[act]
        return False

    # --- State Handler ---
    
    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators

        if entity not in sensors and entity not in actuators:
            self.log_info(f"Ignoriere Zustandsänderung für unbekanntes Entity: {entity}")
            return

        self.log_info(f"Handling state change for: {entity} | New: {new}, Old: {old}")

        if entity in actuators:
            if self.is_blocked(entity):
                return
            self.log_manual_action(entity, new)

        if entity in sensors:
            df_sen_states = self.create_rule_from_state(self.get_state())
            for act, model in self.act_model_set.items():
                if act in self.get_enabled_actuators():
                    prediction = model.predict(df_sen_states)
                    self.log_info(f"Prediction für {act}: {prediction}")
                    if self.verify_rules(act, df_sen_states, prediction, self.get_rules_from_db()):
                        self.handle_action(act, prediction)

