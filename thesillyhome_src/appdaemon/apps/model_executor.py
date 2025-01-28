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
        self.automation_triggered = set()
        self.switch_logs = {}
        self.blocked_actuators = {}
        if not os.path.exists(self.states_db):
            self.init_db()
        self.log("TheSillyHome Model Executor initialized!")

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
            db_rules_engine.to_sql("rules_engine", con=con, if_exists="replace", index=False)

    def unverified_features(self, feature_list):
        feature_list = self.get_new_feature_list(feature_list, "hour_")
        feature_list = self.get_new_feature_list(feature_list, "last_state_")
        feature_list = self.get_new_feature_list(feature_list, "weekday_")
        feature_list = self.get_new_feature_list(feature_list, "switch")
        return feature_list

    def log_automatic_action(self, act, action):
        if self.is_blocked(act):
            self.log(f"Automatische Aktion blockiert: {act} wurde nicht {action}.", level="WARNING")
            return
        self.track_switch(act)
        self.log(f"Automatisch: {act} wurde {action}.", level="INFO")

    def log_manual_action(self, act, state):
        now = datetime.datetime.now()
        if act in self.switch_logs:
            recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 90]
            if recent_switches:
                block_duration = min(1800, 300 + len(recent_switches) * 60)
                self.blocked_actuators[act] = now + datetime.timedelta(seconds=block_duration)
                self.log(f"Manuell: {act} wurde geändert auf {state}. {act} ist jetzt für {block_duration} Sekunden blockiert.", level="WARNING")
                return
        self.blocked_actuators[act] = now + datetime.timedelta(seconds=900)

    def is_blocked(self, act):
        if act in self.blocked_actuators:
            unblock_time = self.blocked_actuators[act]
            if datetime.datetime.now() < unblock_time:
                return True
            del self.blocked_actuators[act]
            self.log(f"{act} wurde freigegeben.", level="INFO")
        return False

    def track_switch(self, act):
        MAX_BLOCK_DURATION = 1800
        MIN_BLOCK_DURATION = 300
        ADDITIONAL_BLOCK_PER_SWITCH = 60
        now = datetime.datetime.now()
        if act not in self.switch_logs:
            self.switch_logs[act] = deque(maxlen=10)
        self.switch_logs[act].append(now)
        recent_switches = [t for t in self.switch_logs[act] if (now - t).total_seconds() <= 30]
        if len(recent_switches) > 6:
            block_duration = min(MAX_BLOCK_DURATION, MIN_BLOCK_DURATION + len(recent_switches) * ADDITIONAL_BLOCK_PER_SWITCH)
            self.blocked_actuators[act] = now + datetime.timedelta(seconds=block_duration)
            self.log(f"{act} wurde wegen häufiger Schaltungen für {block_duration} Sekunden blockiert.", level="ERROR")

    def verify_rules(self, act, rules_to_verify, prediction, all_rules):
        all_rules = all_rules[all_rules["entity_id"] == act]
        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify, how="inner")
            if len(matching_rule) == 2 or (len(matching_rule) == 1 and matching_rule["state"].iloc[0] != prediction):
                return False
        return True

    def add_rules(self, training_time, actuator, new_state, new_rule, all_rules):
        utc = pytz.UTC
        last_states_tmp = {k: v for k, v in self.last_states.items() if k in tsh_config.devices and k != actuator}
        current_states_tmp = {k: v for k, v in self.get_state().items() if k in tsh_config.devices and k != actuator}
        states_no_change = last_states_tmp == current_states_tmp
        last_update_time = datetime.datetime.strptime(self.last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z")
        now_minus_training_time = utc.localize(datetime.datetime.now() - datetime.timedelta(seconds=training_time))
        if states_no_change and self.last_states[actuator]["state"] != new_state and last_update_time > now_minus_training_time:
            new_rule["state"] = np.where(new_rule["state"] == "on", 1, 0)
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()
            if not new_all_rules.equals(all_rules):
                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append", index=False)

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
        return sorted(list(set(base_columns) - {"entity_id", "state", "duplicate"}))

    def get_new_feature_list(self, feature_list, device):
        return sorted([f for f in feature_list if not f.startswith(device)])

def state_handler(self, entity, attribute, old, new, kwargs):
    sensors = tsh_config.sensors
    actuators = tsh_config.actuators
    devices = tsh_config.devices
    all_states = self.get_state()

    if entity not in devices or self.is_blocked(entity):
        return

    feature_list = self.get_base_columns()
    # Erstelle eine DataFrame und füge explizit eine Zeile mit Standardwerten hinzu
    current_state_base = pd.DataFrame(columns=feature_list)
    current_state_base.loc[0] = [0] * len(feature_list)  # Initialisiert alle Werte auf 0
    df_sen_states = copy.deepcopy(current_state_base)

    for sensor in sensors:
        true_state = self.get_state(entity_id=sensor)
        if f"{sensor}_{true_state}" in df_sen_states.columns:
            df_sen_states[f"{sensor}_{true_state}"] = 1

    now = datetime.datetime.now()
    df_sen_states[f"hour_{now.hour}"] = 1
    df_sen_states[f"weekday_{now.weekday()}"] = 1

    with sql.connect(self.states_db) as con:
        try:
            all_rules = pd.read_sql("SELECT * FROM rules_engine", con=con).drop(columns=["index"])
        except Exception as e:
            all_rules = pd.DataFrame(columns=["entity_id", "state"])
            self.log(f"Keine Regeln gefunden: {e}", level="WARNING")

    enabled_actuators = self.read_actuators()

    if entity in actuators:
        new_rule = df_sen_states.copy()
        new_rule = new_rule[self.get_new_feature_list(feature_list, entity)]
        new_rule["entity_id"] = entity
        new_rule["state"] = new
        self.add_rules(20, entity, new, new_rule, all_rules)

    if entity in sensors:
        for act, model in self.act_model_set.items():
            if act in enabled_actuators:
                df_sen_states_less = df_sen_states[self.get_new_feature_list(feature_list, act)]
                prediction = model.predict(df_sen_states_less)
                rule_to_verify = df_sen_states_less.copy()
                rule_to_verify["entity_id"] = act

                if self.verify_rules(act, rule_to_verify, prediction, all_rules):
                    if prediction == 1 and all_states[act]["state"] != "on":
                        self.turn_on(act)
                        self.track_switch(act)
                        self.log_automatic_action(act, "eingeschaltet")
                    elif prediction == 0 and all_states[act]["state"] != "off":
                        self.turn_off(act)
                        self.track_switch(act)
                        self.log_automatic_action(act, "ausgeschaltet")

    for act in actuators:
        current_state = all_states[act]["state"]
        if act not in self.last_states or self.last_states[act]["state"] != current_state:
            if act in self.automation_triggered:
                self.automation_triggered.remove(act)
            else:
                self.log_manual_action(act, current_state)

    self.last_states = all_states

