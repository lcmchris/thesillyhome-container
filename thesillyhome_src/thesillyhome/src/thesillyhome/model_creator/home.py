import os
import json
import datetime
import pandas as pd
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import precision_score, recall_score
from sqlalchemy import create_engine

# home.py
class HomeDB:
    def __init__(self, config):
        self.config = config
        self.mydb = self.connect_db()

    def connect_db(self):
        if self.config["db_type"] == "postgres":
            connection_string = f"postgresql+psycopg2://{self.config['db_username']}:{self.config['db_password']}@{self.config['db_host']}:{self.config['db_port']}/{self.config['db_database']}"
        else:
            connection_string = f"mysql+pymysql://{self.config['db_username']}:{self.config['db_password']}@{self.config['db_host']}:{self.config['db_port']}/{self.config['db_database']}"
        return create_engine(connection_string, echo=False)

    def fetch_data(self):
        query = """
            SELECT states.state_id, states_meta.entity_id, states.state, states.last_updated_ts
            FROM states
            JOIN states_meta ON states.metadata_id = states_meta.metadata_id
            WHERE states.state != 'unavailable'
            ORDER BY states.last_updated_ts DESC
            LIMIT 100000;
        """
        return pd.read_sql(query, con=self.mydb)

# learning_model.py
class LearningModel:
    def __init__(self, config):
        self.config = config
        self.metrics = []

    def train_model(self, data):
        actuators = data["entity_id"].unique()
        for actuator in actuators:
            df = data[data["entity_id"] == actuator]
            if len(df) < 30:
                continue

            X = df.drop(columns=["state", "entity_id"])
            y = df["state"]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

            model = DecisionTreeClassifier()
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            precision = precision_score(y_test, y_pred, average="binary")
            recall = recall_score(y_test, y_pred, average="binary")

            self.metrics.append({
                "actuator": actuator,
                "precision": precision,
                "recall": recall
            })

# model_executor.py
class ModelExecutor:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.manual_override = {}
        self.metrics = {}
        self.load_models()

    def load_models(self):
        for actuator in self.config["actuators"]:
            path = os.path.join(self.config["model_dir"], f"{actuator}.pkl")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    self.models[actuator] = pickle.load(f)

    def execute(self, entity, new_state):
        if self.manual_override.get(entity, False):
            return

        if entity in self.models:
            model = self.models[entity]
            prediction = model.predict([[new_state]])[0]
            if prediction != new_state:
                self.manual_override[entity] = True
                self.deactivate_model(entity)

    def deactivate_model(self, entity):
        self.models.pop(entity, None)
