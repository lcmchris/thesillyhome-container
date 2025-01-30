import appdaemon.plugins.hass.hassapi as hass
import pickle
import pandas as pd
import copy
import os.path
import datetime
import sqlite3 as sql
import numpy as np
import json
from collections import deque

import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    def initialize(self):
        self.log("Initializing TheSillyHome Model Executor...")

        # Lade Sensoren und Aktoren aus der Konfiguration, mit Fallback auf leere Listen bei Fehlern
        self.sensors = getattr(tsh_config, 'sensors_id', [])
        self.actuators = getattr(tsh_config, 'actuactors_id', [])

        if not self.sensors or not self.actuators:
            self.log("Fehler beim Laden der Sensoren oder Aktoren. Überprüfe die Konfiguration!", level="ERROR")
            return

        self.listen_to_devices()

        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.switch_logs = {}
        self.blocked_actuators = {}
        self.init_db()

        self.log("Initialization complete.")

    def listen_to_devices(self):
        """Set up state listeners for all sensors and actuators."""
        for entity in self.sensors + self.actuators:
            self.listen_state(self.state_handler, entity)

    def load_models(self):
        """Lädt die Modelle basierend auf den in der Konfiguration definierten Aktoren."""
        act_model_set = {}
        for act in self.actuators:
            model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
            if os.path.isfile(model_path):
                with open(model_path, "rb") as file:
                    act_model_set[act] = pickle.load(file)
            else:
                self.log(f"Kein Modell für {act} gefunden.", level="WARNING")
        return act_model_set

    def init_db(self):
        """Initialisiert die SQLite-Datenbank für die Regeln."""
        with sql.connect(self.states_db) as con:
            feature_list = self.get_base_columns()
            feature_list = self.unverified_features(feature_list)

            db_rules_engine = pd.DataFrame(columns=feature_list)
            db_rules_engine.loc[0] = 1
            db_rules_engine["entity_id"] = "dummy"
            db_rules_engine["state"] = 1

            try:
                db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace")
                self.log("Initialized rules engine DB")
            except Exception as e:
                self.log(f"Fehler bei der DB-Initialisierung: {str(e)}", level="WARNING")

    def state_handler(self, entity, attribute, old, new, kwargs):
        """Verarbeitet Zustandsänderungen für Sensoren und Aktoren."""
        if entity not in self.sensors + self.actuators:
            self.log(f"Ignoriere Zustandsänderung für unbekanntes Entity: {entity}")
            return

        now = datetime.datetime.now()

        if entity in self.sensors:
            self.handle_sensor_change(entity)

        if entity in self.actuators:
            self.handle_actuator_change(entity, new)

    def handle_sensor_change(self, sensor):
        """Behandelt Änderungen an Sensoren."""
        df_sen_states = self.create_rule_from_state(self.get_state())
        for act, model in self.act_model_set.items():
            if act in self.read_enabled_actuators():
                prediction = model.predict(df_sen_states)
                self.log(f"Prediction für {act}: {prediction}")
                if self.verify_prediction(act, df_sen_states, prediction):
                    self.log(f"Schalte {act} entsprechend der Vorhersage.")
                    self.execute_prediction(act, prediction)

    def handle_actuator_change(self, actuator, new_state):
        """Behandelt Änderungen an Aktoren."""
        if self.is_blocked(actuator):
            self.log(f"Aktor {actuator} ist blockiert und wird nicht geschaltet.", level="WARNING")
            return
        self.log_manual_action(actuator, new_state)

    def execute_prediction(self, actuator, prediction):
        """Schaltet den Aktor basierend auf der Vorhersage ein oder aus."""
        current_state = self.get_state(entity_id=actuator)
        if prediction == 1 and current_state != "on":
            self.turn_on(actuator)
        elif prediction == 0 and current_state != "off":
            self.turn_off(actuator)

    def verify_prediction(self, actuator, df_sen_states, prediction):
        """Überprüft die Vorhersage anhand der gespeicherten Regeln."""
        with sql.connect(self.states_db) as con:
            all_rules = pd.read_sql("SELECT * FROM rules_engine", con)
        all_rules = all_rules.drop(columns=["index"], errors="ignore")
        rules_to_verify = df_sen_states.copy()
        rules_to_verify["entity_id"] = actuator
        return self.verify_rules(actuator, rules_to_verify, prediction, all_rules)

    def read_enabled_actuators(self):
        """Liest die aktuell aktivierten Aktoren aus der Konfigurationsdatei."""
        enabled_actuators = set()
        try:
            with open("/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r") as f:
                metrics_data = json.load(f)
            for metric in metrics_data:
                if metric.get("model_enabled", False):
                    enabled_actuators.add(metric["actuator"])
        except FileNotFoundError:
            self.log("Konfigurationsdatei für Aktivierungsstatus nicht gefunden.", level="WARNING")
        return enabled_actuators

    def log_manual_action(self, act, state):
        """Protokolliert manuelle Änderungen und erstellt neue Regeln."""
        now = datetime.datetime.now()
        current_states = self.get_state()
        new_rule = self.create_rule_from_state(current_states)
        new_rule["entity_id"] = act
        new_rule["state"] = 1 if state == "on" else 0

        with sql.connect(self.states_db) as con:
            new_rule.to_sql("rules_engine", con, if_exists="append")

    def get_base_columns(self):
        """Gibt die Basis-Features zurück."""
        return pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns

    def create_rule_from_state(self, current_states):
        """Erstellt eine Regel aus dem aktuellen Zustand der Sensoren."""
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
