# Library imports
import string
import appdaemon.plugins.hass.hassapi as hass
import pickle
import pandas as pd
import os
import logging
import datetime
import sqlite3 as sql
import numpy as np
from collections import deque
from sklearn.exceptions import NotFittedError

import thesillyhome.model_creator.read_config_json as tsh_config


class ModelExecutorV2(hass.Hass):
    def initialize(self):
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.metrics_file = "/thesillyhome_src/frontend/static/data/metrics_matrix.json"
        self.switch_logs = {}
        self.blocked_actuators = {}
        self.init_db()
        self.log_info("ModelExecutorV2 initialized.")

    ### --- Logging functions --- ###
    def log_info(self, message):
        self.log(message, level="INFO")

    def log_warning(self, message):
        self.log(message, level="WARNING")

    def log_error(self, message):
        self.log(message, level="ERROR")

    ### --- Database and model handling --- ###
    def load_models(self):
        models = {}
        actuators = tsh_config.actuators
        for act in actuators:
            model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
            if os.path.isfile(model_path):
                with open(model_path, "rb") as file:
                    models[act] = pickle.load(file)
            else:
                self.log_warning(f"No model found for actuator: {act}")
        return models

    def init_db(self):
        feature_list = self.get_base_columns()
        rules_engine_df = pd.DataFrame(columns=feature_list)
        rules_engine_df.loc[0] = 1
        rules_engine_df["entity_id"] = "dummy"
        rules_engine_df["state"] = 1

        with sql.connect(self.states_db) as con:
            try:
                rules_engine_df.to_sql("rules_engine", con=con, if_exists="replace")
                self.log_info("Initialized rules engine DB.")
            except Exception as e:
                self.log_warning(f"Could not initialize rules engine DB: {e}")

    def get_base_columns(self):
        return pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns

    ### --- State handling and rule management --- ###
    def create_rule_from_state(self, current_states):
        feature_list = self.get_base_columns()
        rule_data = pd.DataFrame(columns=feature_list)
        rule_data.loc[0] = 0

        now = datetime.datetime.now()
        for entity, value in current_states.items():
            if f"{entity}_{value}" in rule_data.columns:
                rule_data.at[0, f"{entity}_{value}"] = 1
        rule_data[f"hour_{now.hour}"] = 1
        rule_data[f"weekday_{now.weekday()}"] = 1

        return rule_data

    def add_rule(self, actuator, state):
        current_states = self.get_state()
        new_rule = self.create_rule_from_state(current_states)
        new_rule["entity_id"] = actuator
        new_rule["state"] = state

        with sql.connect(self.states_db) as con:
            new_rule.to_sql("rules_engine", con=con, if_exists="append")
        self.log_info(f"Added new rule for {actuator}, state: {state}.")

    def track_switch(self, act):
        now = datetime.datetime.now()
        if act not in self.switch_logs:
            self.switch_logs[act] = deque(maxlen=10)
        self.switch_logs[act].append(now)

        recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 30]
        if len(recent_switches) > 6:
            self.blocked_actuators[act] = now + datetime.timedelta(seconds=1800)
            self.log_error(f"{act} blocked for 1800 seconds due to excessive switching.")

    def is_blocked(self, act):
        if act in self.blocked_actuators:
            unblock_time = self.blocked_actuators[act]
            if datetime.datetime.now() < unblock_time:
                self.log_warning(f"{act} is currently blocked until {unblock_time}.")
                return True
            else:
                del self.blocked_actuators[act]
        return False

    ### --- Model execution and prediction --- ###
    def predict_state(self, model, sensor_data):
        try:
            prediction = model.predict(sensor_data)
            return prediction
        except NotFittedError:
            self.log_warning("Model not fitted. Skipping prediction.")
            return None
        except Exception as e:
            self.log_error(f"Error during prediction: {e}")
            return None

    def handle_prediction(self, actuator, prediction, current_state):
        if prediction == 1 and current_state != "on":
            if not self.is_blocked(actuator):
                self.log_info(f"Turning on {actuator}.")
                self.turn_on(actuator)
                self.track_switch(actuator)
                self.add_rule(actuator, 1)
        elif prediction == 0 and current_state != "off":
            if not self.is_blocked(actuator):
                self.log_info(f"Turning off {actuator}.")
                self.turn_off(actuator)
                self.track_switch(actuator)
                self.add_rule(actuator, 0)

    ### --- State handler --- ###
    def state_handler(self, entity, attribute, old, new, kwargs):
        self.log_info(f"Handling state change for: {entity}")
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators

        if entity in sensors:
            sensor_data = self.create_rule_from_state(self.get_state())

            for actuator, model in self.act_model_set.items():
                if actuator in self.read_enabled_actuators():
                    prediction = self.predict_state(model, sensor_data)
                    if prediction is not None:
                        current_state = self.get_state(entity_id=actuator)["state"]
                        self.handle_prediction(actuator, prediction[0], current_state)

    def read_enabled_actuators(self):
        with open(self.metrics_file, "r") as f:
            metrics_data = json.load(f)
        return {metric["actuator"] for metric in metrics_data if metric["model_enabled"]}
