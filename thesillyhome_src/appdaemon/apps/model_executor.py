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
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
        self.scores = {act: 0.5 for act in tsh_config.actuators}
        self.automation_block = {}  # Track block status for automation
        self.automation_history = {}  # Track state change history for each actuator
        self.automated_actions = {}  # Track automated actions for each actuator
        self.manual_intervention_times = {}  # Track manual interventions with timestamps
        self.init_db()
        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome Model Executor fully initialized!")

    def read_actuators(self):
        enabled_actuators = set()
        with open(
            "/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r"
        ) as f:
            metrics_data = json.load(f)
        for metric in metrics_data:
            if metric["model_enabled"]:
                enabled_actuators.add(metric["actuator"])
        self.log(f"Enabled Actuators: {enabled_actuators}")
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

    def verify_rules(
        self,
        act: string,
        rules_to_verify: pd.DataFrame,
        prediction: int,
        all_rules: pd.DataFrame,
    ):
        t = time.process_time()
        all_rules = all_rules[all_rules["entity_id"] == act]
        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify)
            assert len(matching_rule) in [0, 1, 2], "More than 2 matching rules."
            rules_state = matching_rule["state"].values

            if len(matching_rule) == 2:
                self.log(f"--- These set of features are ambiguous. Do nothing.")
                return False

            elif (len(matching_rule) == 1) and (rules_state != prediction):
                self.log(
                    f"--- This will not be executed as it is part of the excluded rules."
                )
                return False

            else:
                self.log("--- No matching rules")
                return True
        else:
            self.log(f"--- No matching rules, empty DB for {act}")
            return True

    def add_rules(
        self,
        training_time: datetime.datetime,
        actuator: string,
        new_state: int,
        new_rule: pd.DataFrame,
        all_rules: pd.DataFrame,
    ):
        t = time.process_time()

        utc = pytz.UTC
        last_states = self.last_states

        last_states_tmp = last_states.copy()
        current_states_tmp = self.get_state()
        last_states_tmp = {
            your_key: last_states_tmp[your_key] for your_key in tsh_config.devices
        }
        current_states_tmp = {
            your_key: current_states_tmp[your_key] for your_key in tsh_config.devices
        }
        del last_states_tmp[actuator]
        del current_states_tmp[actuator]

        states_no_change = last_states_tmp == current_states_tmp

        last_update_time = datetime.datetime.strptime(
            last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        now_minus_training_time = utc.localize(
            datetime.datetime.now() - datetime.timedelta(seconds=training_time)
        )
        self.log(
            f"---states_no_change: {states_no_change}, last_state: {last_states[actuator]['state']} new_state: {new_state}"
        )

        if (
            states_no_change
            and last_states[actuator]["state"] != new_state
            and last_update_time > now_minus_training_time
        ):
            new_rule["state"] = np.where(new_rule["state"] == "on", 1, 0)
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()

            if not new_all_rules.equals(all_rules):
                self.log(f"---Adding new rule for {actuator}")

                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")
            else:
                self.log(f"---Rule already exists for {actuator}")
        else:
            self.log(f"---Rules not added")
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
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.states_db = "/thesillyhome_src/appdaemon/apps/tsh.db"
        self.last_states = self.get_state()
        self.last_event_time = datetime.datetime.now()
        self.scores = {act: 0.5 for act in tsh_config.actuators}
        self.automation_block = {}  # Track block status for automation
        self.automation_history = {}  # Track state change history for each actuator
        self.automated_actions = {}  # Track automated actions for each actuator
        self.manual_intervention_times = {}  # Track manual interventions with timestamps
        self.init_db()
        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome Model Executor fully initialized!")

    def read_actuators(self):
        enabled_actuators = set()
        with open(
            "/thesillyhome_src/frontend/static/data/metrics_matrix.json", "r"
        ) as f:
            metrics_data = json.load(f)
        for metric in metrics_data:
            if metric["model_enabled"]:
                enabled_actuators.add(metric["actuator"])
        self.log(f"Enabled Actuators: {enabled_actuators}")
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

    def verify_rules(
        self,
        act: string,
        rules_to_verify: pd.DataFrame,
        prediction: int,
        all_rules: pd.DataFrame,
    ):
        t = time.process_time()
        all_rules = all_rules[all_rules["entity_id"] == act]
        if not all_rules.empty:
            matching_rule = all_rules.merge(rules_to_verify)
            assert len(matching_rule) in [0, 1, 2], "More than 2 matching rules."
            rules_state = matching_rule["state"].values

            if len(matching_rule) == 2:
                self.log(f"--- These set of features are ambiguous. Do nothing.")
                return False

            elif (len(matching_rule) == 1) and (rules_state != prediction):
                self.log(
                    f"--- This will not be executed as it is part of the excluded rules."
                )
                return False

            else:
                self.log("--- No matching rules")
                return True
        else:
            self.log(f"--- No matching rules, empty DB for {act}")
            return True

    def add_rules(
        self,
        training_time: datetime.datetime,
        actuator: string,
        new_state: int,
        new_rule: pd.DataFrame,
        all_rules: pd.DataFrame,
    ):
        t = time.process_time()

        utc = pytz.UTC
        last_states = self.last_states

        last_states_tmp = last_states.copy()
        current_states_tmp = self.get_state()
        last_states_tmp = {
            your_key: last_states_tmp[your_key] for your_key in tsh_config.devices
        }
        current_states_tmp = {
            your_key: current_states_tmp[your_key] for your_key in tsh_config.devices
        }
        del last_states_tmp[actuator]
        del current_states_tmp[actuator]

        states_no_change = last_states_tmp == current_states_tmp

        last_update_time = datetime.datetime.strptime(
            last_states[actuator]["last_updated"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        now_minus_training_time = utc.localize(
            datetime.datetime.now() - datetime.timedelta(seconds=training_time)
        )
        self.log(
            f"---states_no_change: {states_no_change}, last_state: {last_states[actuator]['state']} new_state: {new_state}"
        )

        if (
            states_no_change
            and last_states[actuator]["state"] != new_state
            and last_update_time > now_minus_training_time
        ):
            new_rule["state"] = np.where(new_rule["state"] == "on", 1, 0)
            new_all_rules = pd.concat([all_rules, new_rule]).drop_duplicates()

            if not new_all_rules.equals(all_rules):
                self.log(f"---Adding new rule for {actuator}")

                with sql.connect(self.states_db) as con:
                    new_rule.to_sql("rules_engine", con=con, if_exists="append")
            else:
                self.log(f"---Rule already exists for {actuator}")
        else:
            self.log(f"---Rules not added")
