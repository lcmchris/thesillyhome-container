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

import thesillyhome.model_creator.read_config_json as tsh_config

class ModelExecutor(hass.Hass):
    def initialize(self):
        try:
            self.handle = self.listen_state(self.state_handler)
            self.act_model_set = self.load_models()
            self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
            self.last_states = self.get_state()
            self.last_event_time = datetime.datetime.now(pytz.UTC)
            self.manual_interventions = {}  # {actuator: count}
            self.blocked_actuators = {}  # {actuator: block_end_time}
            self.last_action_by_ai = {}  # {actuator: True/False}
            self.init_db()
            self.log("Initialization complete for ModelExecutor.")
        except Exception as e:
            self.log(f"Error during initialization: {e}", level="ERROR")

    def read_actuators(self):
        enabled_actuators = set()
        try:
            with open(
                "/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r"
            ) as f:
                metrics_data = json.load(f)
            for metric in metrics_data:
                if metric["model_enabled"]:
                    enabled_actuators.add(metric["actuator"])
            self.log(f"Enabled Actuators: {enabled_actuators}")
        except Exception as e:
            self.log(f"Error reading actuators: {e}", level="ERROR")
        return enabled_actuators

    def init_db(self):
        try:
            with sql.connect(self.states_db) as con:
                feature_list = self.get_base_columns()
                feature_list = self.unverified_features(feature_list)
                db_rules_engine = pd.DataFrame(columns=feature_list)
                db_rules_engine.loc[0] = 1
                db_rules_engine["entity_id"] = "dummy"
                db_rules_engine["state"] = 1

                self.log(f"Initialized rules engine DB.", level="INFO")
                try:
                    db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace")
                except Exception as e:
                    self.log(f"DB already exists or error occurred: {e}", level="INFO")
        except Exception as e:
            self.log(f"Error initializing DB: {e}", level="ERROR")

    def is_manual_intervention(self, entity, new_state):
        try:
            last_updated = self.get_state(entity_id=entity, attribute="last_changed")
            now = datetime.datetime.now(pytz.UTC)
            last_updated = datetime.datetime.strptime(
                last_updated, "%Y-%m-%dT%H:%M:%S.%f%z"
            )

            time_diff = now - last_updated
            was_ai = self.last_action_by_ai.get(entity, False)

            if was_ai:
                self.log(f"Change detected for {entity}, but it was triggered by AI.", level="DEBUG")
                return False

            self.log(f"Manual intervention detected for {entity}.", level="DEBUG")
            return time_diff.total_seconds() > 2
        except Exception as e:
            self.log(f"Error in is_manual_intervention: {e}", level="ERROR")
            return False

    def state_handler(self, entity, attribute, old, new, kwargs):
        try:
            if not hasattr(self, "blocked_actuators"):
                self.blocked_actuators = {}

            sensors = tsh_config.sensors
            actuators = tsh_config.actuators
            now = datetime.datetime.now(pytz.UTC)

            if entity in actuators:
                if old != new:
                    if self.is_manual_intervention(entity, new):
                        self.manual_interventions[entity] = (
                            self.manual_interventions.get(entity, 0) + 1
                        )

                        if self.manual_interventions[entity] >= 3:
                            self.blocked_actuators[entity] = now + datetime.timedelta(seconds=90)
                            self.manual_interventions[entity] = 0
                            self.log(f"Blocking {entity} for 90 seconds due to manual interventions.")

                    if entity in self.blocked_actuators and now < self.blocked_actuators[entity]:
                        self.log(f"{entity} is blocked. Ignoring state change.")
                        return

                    self.last_action_by_ai[entity] = False

            if entity in sensors or entity in actuators:
                self.process_state_change(entity, old, new)
        except Exception as e:
            self.log(f"Error in state_handler: {e}", level="ERROR")

    def process_state_change(self, entity, old, new):
        try:
            feature_list = self.get_base_columns()
            df_sen_states = pd.DataFrame(columns=feature_list)
            df_sen_states.loc[0] = 0

            for sensor in tsh_config.sensors:
                true_state = self.get_state(entity_id=sensor)
                if f"{sensor}_{true_state}" in df_sen_states.columns:
                    df_sen_states[f"{sensor}_{true_state}"] = 1

            df_sen_states[f"hour_{datetime.datetime.now(pytz.UTC).hour}"] = 1

            if entity in self.act_model_set:
                model = self.act_model_set[entity]
                prediction = model.predict(df_sen_states)

                if prediction != new:
                    self.log(f"Prediction for {entity} differs from new state. Updating rules.", level="INFO")
                    self.update_rules(entity, new, df_sen_states, prediction)
                else:
                    self.log(f"Prediction for {entity} matches new state. Executing action.", level="INFO")
                    self.execute_action(entity, prediction)
        except Exception as e:
            self.log(f"Error in process_state_change: {e}", level="ERROR")

    def execute_action(self, entity, prediction):
        try:
            if prediction == 1:
                self.log(f"Turning on {entity}.", level="INFO")
                self.turn_on(entity)
                self.last_action_by_ai[entity] = True
            elif prediction == 0:
                self.log(f"Turning off {entity}.", level="INFO")
                self.turn_off(entity)
                self.last_action_by_ai[entity] = True
        except Exception as e:
            self.log(f"Error executing action for {entity}: {e}", level="ERROR")

    def update_rules(self, entity, new_state, state_data, prediction):
        try:
            with sql.connect(self.states_db) as con:
                rules = pd.read_sql("SELECT * FROM rules_engine", con=con)

                new_rule = state_data.copy()
                new_rule["entity_id"] = entity
                new_rule["state"] = new_state

                feedback_weight = 0.1  # Gewichtung der Korrektur
                precision_loss = 1 - feedback_weight

                if not rules.equals(new_rule):
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")
                    self.log(f"Rules updated for {entity}. Precision might be affected: {precision_loss:.2%}", level="INFO")

                    # Apply precision loss to adjust model weights dynamically
                    if entity in self.act_model_set:
                        model = self.act_model_set[entity]
                        model_weights = model.coef_ * feedback_weight
                        model.intercept_ *= feedback_weight
                        model.coef_ = model_weights
                        self.log(f"Adjusted model weights for {entity} to account for feedback.", level="INFO")
                else:
                    self.log(f"No new rules needed for {entity}.", level="INFO")
        except Exception as e:
            self.log(f"Error updating rules for {entity}: {e}", level="ERROR")

    def load_models(self):
        try:
            actuators = tsh_config.actuators
            models = {}
            for act in actuators:
                model_path = f"{tsh_config.data_dir}/model/{act}/best_model.pkl"
                if os.path.isfile(model_path):
                    with open(model_path, "rb") as f:
                        models[act] = pickle.load(f)
            return models
        except Exception as e:
            self.log(f"Error loading models: {e}", level="ERROR")
            return {}

    def get_base_columns(self):
        try:
            return pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns.tolist()
        except Exception as e:
            self.log(f"Error in get_base_columns: {e}", level="ERROR")
            return []
