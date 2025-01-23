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
        self.last_automation_trigger = {}  # Cache für Aktionen, die nicht manuell sind

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

        if enabled_actuators != getattr(self, "cached_actuators", set()):
            self.log(f"Enabled Actuators: {enabled_actuators}")
            self.cached_actuators = enabled_actuators
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
        now = datetime.datetime.now()

        if entity in actuators:
            device_state = self.device_states.get(entity, {"state": "off", "changes": 0, "last_changed": datetime.datetime.min})
            manual_intervention = False

            # Prüfen, ob die Statusänderung von der KI ausgelöst wurde
            ki_triggered = self.manual_override.get(entity, False)

            # Prüfen, ob die Statusänderung durch eine bekannte Automation ausgelöst wurde
            automation_triggered = self.last_automation_trigger.get(entity, False)
            if automation_triggered:
                self.log(f"---{entity} wurde durch Automation ausgelöst (z. B. Sensor).")
                self.last_automation_trigger[entity] = False  # Automatisierung zurücksetzen

            # Prüfen auf manuellen Eingriff
            if not ki_triggered and not automation_triggered and old != new:
                self.log(f"---Manueller Eingriff erkannt: {entity} wurde manuell geschaltet.")
                manual_intervention = True
                self.act_model_set[entity].probability_threshold += 0.01
                self.act_model_set[entity].probability_threshold = min(self.act_model_set[entity].probability_threshold, 1.0)
            
            elif ki_triggered:
                device_state["changes"] += 1
                if device_state["changes"] > 3:
                    self.log(f"---Maximale Schaltversuche durch KI für {entity} erreicht. Blockiere KI für 90 Sekunden.")
                    self.manual_override[entity] = True
                    self.run_in(self.clear_override, 90, entity=entity)
                    self.act_model_set[entity].probability_threshold -= 0.03
                    self.act_model_set[entity].probability_threshold = max(self.act_model_set[entity].probability_threshold, 0.5)
                    return

            # Update Gerätestatus
            device_state["state"] = new
            device_state["last_changed"] = now
            self.device_states[entity] = device_state

        if entity in sensors:
            for act, model in self.act_model_set.items():
                if act in actuators:
                    self.log(f"Prediction sequence for: {act}")
                    
                    prediction = model.predict(pd.DataFrame([self.device_states]))

                    if prediction == 1 and self.get_state(act) != "on":
                        self.log(f"---Turn on {act}")
                        self.turn_on(act)
                        self.last_automation_trigger[act] = True
                    elif prediction == 0 and self.get_state(act) != "off":
                        self.log(f"---Turn off {act}")
                        self.turn_off(act)
                        self.last_automation_trigger[act] = True
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
