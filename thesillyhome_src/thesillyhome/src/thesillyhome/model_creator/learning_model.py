import os
import pickle
import logging
import pandas as pd
import numpy as np
import datetime
import sqlite3 as sql
from collections import deque
import thesillyhome.model_creator.read_config_json as tsh_config
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

class ModelExecutor:
    def initialize(self):
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.automation_triggered = set()
        self.switch_logs = {}
        self.blocked_actuators = {}
        self.init_db()

    def read_actuators(self):
        enabled_actuators = set()
        with open("/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r") as f:
            metrics_data = json.load(f)
        for metric in metrics_data:
            if metric["model_enabled"]:
                enabled_actuators.add(metric["actuator"])
        return enabled_actuators

    def init_db(self):
        with sql.connect(self.states_db) as con:
            feature_list = self.get_base_columns()
            feature_list = self.unverified_features(feature_list)
            db_rules_engine = pd.DataFrame(columns=feature_list)
            db_rules_engine.loc[0] = 1
            db_rules_engine["entity_id"] = "dummy"
            db_rules_engine["state"] = 1
            db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace")

    def extract_sensor_behavior(self, df, sensor_column, related_columns, time_window=5):
        for related in related_columns:
            df[f"{sensor_column}_change_in_{related}"] = df[related].diff(periods=time_window)
        return df

    def classify_sensor_types(self, df, sensor_column, related_columns, model):
        X = df[related_columns]
        return model.predict(X)

    def adjust_sensor_weights(self, X_train, sensor_types):
        for sensor, sensor_type in sensor_types.items():
            if sensor in X_train.columns:
                if sensor_type == "door":
                    X_train[sensor] *= 2
                elif sensor_type == "window":
                    X_train[sensor] *= 0.5
        return X_train

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        actuators = tsh_config.actuators
        float_sensors = tsh_config.float_sensors
        devices = tsh_config.devices

        if entity in devices:
            feature_list = self.get_base_columns()
            current_state_base = pd.DataFrame(columns=feature_list)
            current_state_base.loc[0] = 0

            df_sen_states = current_state_base.copy()
            for sensor in sensors:
                true_state = self.get_state(entity_id=sensor)
                if sensor not in float_sensors and f"{sensor}_{true_state}" in df_sen_states.columns:
                    df_sen_states[sensor + "_" + true_state] = 1
                elif sensor in float_sensors:
                    df_sen_states[sensor] = true_state

            df_sen_states[f"hour_{datetime.datetime.now().hour}"] = 1
            df_sen_states[f"weekday_{datetime.datetime.now().weekday()}"] = 1

            with sql.connect(self.states_db) as con:
                all_rules = pd.read_sql(f"SELECT * FROM rules_engine", con=con).drop(columns=["index"])

            enabled_actuators = self.read_actuators()

            if entity in actuators:
                if self.is_blocked(entity):
                    return
                new_rule = df_sen_states.copy()
                new_rule = new_rule[self.get_new_feature_list(feature_list, entity)]
                new_rule = new_rule[self.unverified_features(new_rule.columns.values.tolist())]
                new_rule["entity_id"] = entity
                new_rule["state"] = new
                self.add_rules(20, entity, new, new_rule, all_rules)

            if entity in sensors:
                for act, model in self.act_model_set.items():
                    if act in enabled_actuators:
                        df_sen_states_less = df_sen_states[self.get_new_feature_list(feature_list, act)]
                        prediction = model.predict(df_sen_states_less)
                        rule_to_verify = df_sen_states_less.copy()
                        rule_to_verify = rule_to_verify[self.unverified_features(rule_to_verify.columns.values.tolist())]
                        rule_to_verify["entity_id"] = act

                        if self.verify_rules(act, rule_to_verify, prediction, all_rules):
                            if prediction == 1 and self.get_state(entity_id=act)["state"] != "on":
                                if not self.is_blocked(act):
                                    self.turn_on(act)
                                    self.track_switch(act)
                                    self.log_automatic_action(act, "eingeschaltet")
                            elif prediction == 0 and self.get_state(entity_id=act)["state"] != "off":
                                if not self.is_blocked(act):
                                    self.turn_off(act)
                                    self.track_switch(act)
                                    self.log_automatic_action(act, "ausgeschaltet")

            for act in actuators:
                current_state = self.get_state(entity_id=act)["state"]
                if act not in self.last_states or self.last_states[act]["state"] != current_state:
                    if act not in self.automation_triggered:
                        self.log_manual_action(act, current_state)

            self.last_states = self.get_state()

    def verify_rules(self, act, rules_to_verify, prediction, all_rules):
        all_rules = all_rules[all_rules["entity_id"] == act]
        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify)
            rules_state = matching_rule["state"].values

            if len(matching_rule) == 2 or (len(matching_rule) == 1 and rules_state != prediction):
                return False
            else:
                return True
        return True

    def add_rules(self, training_time, actuator, new_state, new_rule, all_rules):
        utc = pytz.UTC
        last_states_tmp = {k: self.last_states[k] for k in tsh_config.devices if k in self.last_states}
        current_states_tmp = {k: self.get_state()[k] for k in tsh_config.devices if k in self.get_state()}
        del last_states_tmp[actuator]
        del current_states_tmp[actuator]

        states_no_change = last_states_tmp == current_states_tmp
        last_update_time = datetime.datetime.strptime(self.last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z")
        now_minus_training_time = utc.localize(datetime.datetime.now() - datetime.timedelta(seconds=training_time))

        if states_no_change and self.last_states[actuator]["state"] != new_state and last_update_time > now_minus_training_time:
            new_rule["state"] = np.where(new_rule["state"] == "on", 1, 0)
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()

            if not new_all_rules.equals(all_rules):
                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")

    def load_models(self):
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            if os.path.isfile(f"{tsh_config.data_dir}/model/{act}/best_model.pkl"):
                with open(f"{tsh_config.data_dir}/model/{act}/best_model.pkl", "rb") as pickle_file:
                    act_model_set[act] = pickle.load(pickle_file)
        return act_model_set

    def get_base_columns(self):
        base_columns = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").columns
        base_columns = sorted(list(set(base_columns) - set(["entity_id", "state", "duplicate"])))
        return base_columns

    def get_new_feature_list(self, feature_list, device):
        cur_list = [feature for feature in feature_list if feature.startswith(device)]
        return sorted(list(set(feature_list) - set(cur_list)))

    def unverified_features(self, feature_list):
        feature_list = self.get_new_feature_list(feature_list, "hour_")
        feature_list = self.get_new_feature_list(feature_list, "last_state_")
        feature_list = self.get_new_feature_list(feature_list, "weekday_")
        feature_list = self.get_new_feature_list(feature_list, "switch")
        return feature_list
