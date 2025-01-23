import appdaemon.plugins.hass.hassapi as hass
import pickle
import pandas as pd
import os
import datetime
import sqlite3 as sql
import json
from collections import defaultdict

# Lokale Importe
import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    def initialize(self):
        self.device_states = {}
        self.manual_override = {}
        self.error_log = []
        self.last_automation_trigger = {}
        self.actuation_counts = defaultdict(int)  # Zählt die Schaltvorgänge pro Aktor

        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.init_db()

        # Initialisierung der Gerätezustände
        for device in tsh_config.devices:
            self.device_states[device] = {
                "state": "off",
                "changes": 0,
                "last_changed": datetime.datetime.min
            }

        self.log("TheSillyHome Model Executor fully initialized!")

    def load_models(self):
        """
        Lädt die Modelle für alle Aktoren und setzt den Schwellenwert initial auf 0.5.
        """
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
            if os.path.isfile(model_path):
                with open(model_path, "rb") as pickle_file:
                    model = pickle.load(pickle_file)
                    model.probability_threshold = 0.5  # Initial auf 0.5 setzen
                    act_model_set[act] = model
            else:
                self.log(f"Kein Modell für {act} gefunden. Überspringe.", level="WARNING")
        return act_model_set

    def init_db(self):
        """
        Initialisiert die Datenbank, falls erforderlich.
        """
        db_path = "/thesillyhome_src/appdaemon/apps/tsh.db"
        with sql.connect(db_path) as con:
            feature_list = self.get_base_columns()
            db_rules_engine = pd.DataFrame(columns=feature_list)
            db_rules_engine.loc[0] = 1
            db_rules_engine["entity_id"] = "dummy"
            db_rules_engine["state"] = 1
            try:
                db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace")
            except Exception as e:
                self.log(f"Datenbank bereits initialisiert. Fehler: {e}", level="INFO")

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        enabled_actuators = self.read_actuators()  # Aktivierte Aktoren laden

        if entity not in sensors and entity not in actuators:
            return  # Ignoriere nicht konfigurierte Entitäten

        # Sensoren loggen Statusänderungen
        if entity in sensors and old != new:
            self.log(f"{entity} hat seinen Zustand geändert: {old} -> {new}")

        if entity in actuators:
            # Redundantes Schalten vermeiden
            if old == new:
                return

            # Prüfen, ob der Aktor aktiviert ist
            if entity not in enabled_actuators:
                self.log(f"{entity} ist deaktiviert. Ignoriere Schaltvorgang.", level="DEBUG")
                return

            # KI-Vorhersage und Schalten
            model = self.act_model_set.get(entity)
            if not model:
                self.log(f"Kein Modell für {entity} gefunden.", level="ERROR")
                return

            try:
                prediction = model.predict(pd.DataFrame([self.device_states]))
                if prediction == 1 and self.get_state(entity) != "on":
                    self.turn_on(entity)
                    self.log(f"---Turn on {entity}")
                elif prediction == 0 and self.get_state(entity) != "off":
                    self.turn_off(entity)
                    self.log(f"---Turn off {entity}")
            except Exception as e:
                self.log(f"Fehler bei der Vorhersage für {entity}: {e}", level="ERROR")
