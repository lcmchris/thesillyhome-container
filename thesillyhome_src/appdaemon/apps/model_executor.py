import appdaemon.plugins.hass.hassapi as hass
import pickle
import pandas as pd
import json
import datetime
import sqlite3 as sql
import logging
import copy
from collections import deque

import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):

    def initialize(self):
        self.log("Initializing TheSillyHome Model Executor...")

        # Lade Sensoren und Aktoren aus der Config
        self.sensors = tsh_config.sensors_id
        self.actuators = tsh_config.actuactors_id
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"

        # Setze das Event-Handling nur für relevante Entitäten
        for entity in self.sensors + self.actuators:
            self.listen_state(self.state_handler, entity)

        # Initialisiere Modelle und Schaltlogik
        self.act_model_set = self.load_models()
        self.switch_logs = {}
        self.blocked_actuators = {}

        self.init_db()
        self.log("Initialization complete.")

    def init_db(self):
        """Initialisiere die Datenbank für die Regeln."""
        with sql.connect(self.states_db) as con:
            feature_list = self.get_base_columns()
            db_rules_engine = pd.DataFrame(columns=feature_list)
            db_rules_engine.loc[0] = 0
            db_rules_engine["entity_id"] = "dummy"
            db_rules_engine["state"] = 1

            self.log("Initialized rules engine DB", level="INFO")
            db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace")

    def state_handler(self, entity, attribute, old, new, kwargs):
        """Handler für Zustandsänderungen relevanter Entitäten."""
        if entity in self.sensors:
            self.log_info(f"Verarbeite Sensoränderung: {entity} | Neu: {new}, Alt: {old}")
            self.handle_sensor_state_change(entity, new)
        
        elif entity in self.actuators:
            self.log_info(f"Verarbeite Aktoränderung: {entity} | Neu: {new}, Alt: {old}")
            self.handle_actuator_state_change(entity, new)

    def handle_sensor_state_change(self, entity, new_state):
        """Verarbeitung von Sensoränderungen."""
        df_sen_states = self.create_rule_from_state(self.get_current_states(self.sensors))

        # Modelle ausführen und Aktionen verarbeiten
        for act, model in self.act_model_set.items():
            if act in self.get_enabled_actuators():
                prediction = model.predict(df_sen_states)
                self.log_info(f"Vorhersage für {act}: {prediction}")

                if self.verify_rules(act, df_sen_states, prediction):
                    self.handle_action(act, prediction)

    def handle_actuator_state_change(self, entity, new_state):
        """Verarbeitung manueller Änderungen an Aktoren."""
        if self.is_blocked(entity):
            self.log_info(f"Aktor {entity} ist blockiert. Änderung ignoriert.")
            return

        self.log_manual_action(entity, new_state)

    def handle_action(self, actuator, prediction):
        """Schalte den Aktor basierend auf der Vorhersage ein oder aus."""
        current_state = self.get_state(actuator)
        if prediction == 1 and current_state != "on":
            self.turn_on(actuator)
            self.log_action(actuator, "eingeschaltet")
        elif prediction == 0 and current_state != "off":
            self.turn_off(actuator)
            self.log_action(actuator, "ausgeschaltet")

    def create_rule_from_state(self, current_states):
        """Erstelle eine Regel basierend auf den aktuellen Sensorzuständen."""
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

    def get_current_states(self, entities):
        """Gibt den aktuellen Zustand der angegebenen Entitäten zurück."""
        return {entity: self.get_state(entity) for entity in entities}

    def get_enabled_actuators(self):
        """Liest die aktivierten Aktoren aus der Konfigurationsdatei."""
        return [act for act in self.actuators if self.is_actuator_enabled(act)]

    def is_actuator_enabled(self, actuator):
        """Prüft, ob ein Aktor in der Konfiguration aktiviert ist."""
        with open("/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r") as f:
            metrics_data = json.load(f)
        for metric in metrics_data:
            if metric["actuator"] == actuator and metric["model_enabled"]:
                return True
        return False

    def load_models(self):
        """Lädt die Modelle für die Aktoren."""
        models = {}
        for act in self.actuators:
            model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
            if os.path.isfile(model_path):
                with open(model_path, "rb") as file:
                    models[act] = pickle.load(file)
            else:
                self.log_warning(f"Kein Modell für {act} gefunden.")
        return models

    def verify_rules(self, act, rule_data, prediction):
        """Überprüft die Regeln für den Aktor."""
        with sql.connect(self.states_db) as con:
            all_rules = pd.read_sql("SELECT * FROM rules_engine WHERE entity_id = ?", con, params=(act,))
        
        matching_rule = all_rules.merge(rule_data, how="inner")
        if not matching_rule.empty and matching_rule["state"].iloc[0] != prediction:
            self.log_info(f"Vorhersage für {act} wird verworfen. Regel widerspricht der Vorhersage.")
            return False

        return True

    def log_manual_action(self, actuator, new_state):
        """Logge und speichere eine Regel für eine manuelle Aktion."""
        current_states = self.get_current_states(self.sensors)
        new_rule = self.create_rule_from_state(current_states)
        new_rule["entity_id"] = actuator
        new_rule["state"] = 1 if new_state == "on" else 0

        with sql.connect(self.states_db) as con:
            new_rule.to_sql("rules_engine", con=con, if_exists="append")

    def log_action(self, actuator, action):
        """Loggt eine automatische Aktion."""
        self.log_info(f"Automatisch: {actuator} wurde {action}.")

    def log_info(self, message):
        """Einheitliche Info-Logging-Funktion."""
        self.log(message, level="INFO")

    def log_warning(self, message):
        """Einheitliche Warning-Logging-Funktion."""
        self.log(message, level="WARNING")

    def is_blocked(self, actuator):
        """Überprüft, ob ein Aktor blockiert ist."""
        unblock_time = self.blocked_actuators.get(actuator)
        if unblock_time and datetime.datetime.now() < unblock_time:
            self.log_warning(f"{actuator} ist blockiert bis {unblock_time}.")
            return True
        return False
