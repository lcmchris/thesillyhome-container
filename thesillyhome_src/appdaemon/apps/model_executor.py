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
import threading

class ModelExecutor(hass.Hass):
    def initialize(self):
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
        self.init_db()
        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome Model Executor fully initialized!")

        # Track automatic actions, toggling prevention, and learning
        self.auto_executed = {}  # Tracks if the actuator was controlled automatically
        self.manual_intervention = {}  # Tracks manual intervention
        self.toggle_prevention = {}  # Tracks prevention period for toggling actuators
        self.learning_data = {}  # Tracks correctness of actions for learning

    def prevent_toggle(self, actuator):
        self.toggle_prevention[actuator] = True
        time.sleep(300)  # Prevent toggling for 5 minutes
        self.toggle_prevention[actuator] = False

    def handle_toggle_prevention(self, actuator):
        if actuator not in self.toggle_prevention:
            self.toggle_prevention[actuator] = False

    def is_toggling_prevented(self, actuator):
        return self.toggle_prevention.get(actuator, False)

    def mark_manual_action(self, actuator):
        self.manual_intervention[actuator] = datetime.datetime.now()
        if actuator in self.auto_executed and self.auto_executed[actuator]:
            self.auto_executed[actuator] = False
            self.log(f"Manual action detected for actuator: {actuator}")

    def mark_automatic_action(self, actuator):
        self.auto_executed[actuator] = True
        self.learning_data[actuator] = {
            "start_time": datetime.datetime.now(),
            "valid": None
        }
        self.log(f"Automatic action performed on actuator: {actuator}")

    def evaluate_action(self, actuator):
        if actuator in self.learning_data:
            start_time = self.learning_data[actuator]["start_time"]
            now = datetime.datetime.now()
            time_diff = (now - start_time).total_seconds()

            if actuator in self.manual_intervention:
                manual_time = self.manual_intervention[actuator]
                manual_diff = (manual_time - start_time).total_seconds()
                
                if manual_diff <= 10 and manual_time >= start_time:
                    self.learning_data[actuator]["valid"] = False
                    self.log(f"Learning: Automatic action for {actuator} was incorrect (manual intervention within 10 seconds).", level="WARNING")
                    threading.Thread(target=self.prevent_toggle, args=(actuator,)).start()

                elif manual_diff <= 45 and manual_time >= start_time:
                    self.learning_data[actuator]["valid"] = False
                    self.log(f"Learning: Automatic action for {actuator} was incorrect (manual intervention within 45 seconds).", level="WARNING")

                elif manual_diff > 45:
                    self.learning_data[actuator]["valid"] = True
                    self.log(f"Learning: Automatic action for {actuator} was correct (manual intervention after 45 seconds).", level="INFO")
            else:
                if time_diff > 45:
                    self.learning_data[actuator]["valid"] = True
                    self.log(f"Learning: Automatic action for {actuator} was correct (no manual intervention within 45 seconds).", level="INFO")

            # Save learning result to database
            self.save_learning_to_db(actuator)
            # Retrain model using feedback
            self.retrain_model(actuator)

    def save_learning_to_db(self, actuator):
        try:
            with sql.connect(self.states_db) as con:
                cursor = con.cursor()
                valid = self.learning_data[actuator].get("valid")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO learning_feedback (actuator, valid, timestamp) VALUES (?, ?, ?)",
                    (actuator, valid, timestamp)
                )
                con.commit()
                self.log(f"Learning data for {actuator} saved to database.", level="INFO")
        except Exception as e:
            self.log(f"Error saving learning data for {actuator}: {e}", level="ERROR")

    def retrain_model(self, actuator):
        try:
            self.log(f"Retraining model for actuator: {actuator}", level="INFO")
            with sql.connect(self.states_db) as con:
                feedback_query = "SELECT * FROM learning_feedback WHERE actuator = ?"
                feedback_data = pd.read_sql(feedback_query, con, params=(actuator,))

            # Placeholder: Use feedback_data to retrain the model
            # For simplicity, we assume binary classification: valid = 1, invalid = 0
            if not feedback_data.empty:
                feedback_data["valid"] = feedback_data["valid"].astype(int)
                # Example: Update model using the feedback data
                self.act_model_set[actuator].fit(feedback_data[["timestamp"]], feedback_data["valid"])
                self.log(f"Model for {actuator} updated successfully with feedback.", level="INFO")
            else:
                self.log(f"No feedback data available for actuator: {actuator}", level="WARNING")

        except Exception as e:
            self.log(f"Error retraining model for {actuator}: {e}", level="ERROR")

    def execute_action(self, actuator, action):
        if self.is_toggling_prevented(actuator):
            self.log(f"Action on {actuator} prevented due to toggle prevention.", level="INFO")
            return

        if action == "on":
            self.turn_on(actuator)
            self.mark_automatic_action(actuator)
        elif action == "off":
            self.turn_off(actuator)
            self.mark_automatic_action(actuator)

        # Start evaluation after 45 seconds
        threading.Timer(45, self.evaluate_action, args=(actuator,)).start()

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        float_sensors = tsh_config.float_sensors
        devices = tsh_config.devices
        now = datetime.datetime.now()

        if entity in devices:
            self.log(f"\n")
            self.log(f"<--- {entity} is {new} --->")

            # Get feature list from parsed data header, set all columns to 0
            feature_list = self.get_base_columns()

            current_state_base = pd.DataFrame(columns=feature_list)
            current_state_base.loc[0] = 0

            # Get current state of all sensors for model input
            df_sen_states = copy.deepcopy(current_state_base)
            for sensor in sensors:
                true_state = self.get_state(entity_id=sensor)
                if sensor not in float_sensors:
                    if f"{sensor}_{true_state}" in df_sen_states.columns:
                        df_sen_states[sensor + "_" + true_state] = 1
                elif sensor in float_sensors:
                    if (true_state) in df_sen_states.columns:
                        df_sen_states[sensor] = true_state

            last_states = self.last_states
            all_states = self.get_state()

            # Extract current date
            # datetime object containing current date and time
            df_sen_states[f"hour_{now.hour}"] = 1
            df_sen_states[f"weekday_{now.weekday()}"] = 1
            self.log(
                f"Time is : hour_{now.hour} & weekday_{now.weekday()}", level="DEBUG"
            )

            # Check rules for actuators against rules engine
            with sql.connect(self.states_db) as con:
                all_rules = pd.read_sql(
                    f"SELECT * FROM rules_engine",
                    con=con,
                )
                all_rules = all_rules.drop(columns=["index"])

            enabled_actuators = self.read_actuators()
            if entity in actuators:
                # Adding rules
                new_rule = df_sen_states.copy()
                new_rule = new_rule[self.get_new_feature_list(feature_list, entity)]
                new_rule = new_rule[
                    self.unverified_features(new_rule.columns.values.tolist())
                ]
                new_rule["entity_id"] = entity
                new_rule["state"] = new
                training_time = 10
                self.add_rules(training_time, entity, new, new_rule, all_rules)

            # Execute all models for sensor and set states
            if entity in sensors:
                for act, model in self.act_model_set.items():
                    if act in enabled_actuators:
                        self.log(f"Prediction sequence for: {act}")

                        df_sen_states_less = df_sen_states[
                            self.get_new_feature_list(feature_list, act)
                        ]

                        prediction = model.predict(df_sen_states_less)

                        rule_to_verify = df_sen_states_less.copy()
                        rule_to_verify = rule_to_verify[
                            self.unverified_features(
                                rule_to_verify.columns.values.tolist()
                            )
                        ]
                        rule_to_verify["entity_id"] = act

                        if self.verify_rules(
                            act, rule_to_verify, prediction, all_rules
                        ):
                            # Execute actions
                            if (prediction == 1) and (all_states[act]["state"] != "on"):
                                if not self.is_toggling_prevented(act):
                                    self.log(f"---Turn on {act}")
                                    self.execute_action(act, "on")
                            elif (prediction == 0) and (all_states[act]["state"] != "off"):
                                if not self.is_toggling_prevented(act):
                                    self.log(f"---Turn off {act}")
                                    self.execute_action(act, "off")

                            self.mark_manual_action(act)  # Mark manual if actuator state changes unexpectedly

                    else:
                        self.log("Ignore Disabled actuator")

            self.last_states = self.get_state()
