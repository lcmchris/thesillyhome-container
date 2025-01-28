import logging
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import thesillyhome.model_creator.read_config_json as tsh_config

def train_sensor_type_model(df, sensor_column, related_columns):
    X = df[related_columns]
    y = df[sensor_column].apply(lambda x: "door" if "door" in x else "window" if "window" in x else "other")
    model = DecisionTreeClassifier(max_depth=5)
    model.fit(X, y)
    return model

def adjust_sensor_weights(X_train, sensor_types):
    for sensor, sensor_type in sensor_types.items():
        if sensor in X_train.columns:
            if sensor_type == "door":
                X_train[sensor] *= 2
            elif sensor_type == "window":
                X_train[sensor] *= 0.5
    return X_train

def classify_sensor_types(df, sensor_column, related_columns, model):
    X = df[related_columns]
    return model.predict(X)

def train_all_actuator_models():
    actuators = tsh_config.actuators
    df_act_states = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").reset_index(drop=True)
    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

    model_types = {
        "DecisionTreeClassifier": {
            "classifier": DecisionTreeClassifier,
            "model_kwargs": {"max_depth": 7, "min_samples_split": 5, "min_samples_leaf": 3},
        },
        "LogisticRegression": {
            "classifier": LogisticRegression,
            "model_kwargs": {"max_iter": 10000, "C": 0.5},
        },
        "RandomForestClassifier": {
            "classifier": RandomForestClassifier,
            "model_kwargs": {"n_estimators": 100, "max_depth": 10, "min_samples_split": 5, "min_samples_leaf": 3},
        },
        "SVMClassifier": {
            "classifier": SVC,
            "model_kwargs": {"probability": True, "C": 0.5},
        },
    }

    metrics_matrix = []
    related_columns = ["temperature", "light"]
    print("Available columns in df_act_states:", df_act_states.columns)

    sensor_column = "entity_id"
    sensor_model = train_sensor_type_model(df_act_states, sensor_column, related_columns)

    for actuator in actuators:
        logging.info(f"Training model for {actuator}")
        df_act = df_act_states[df_act_states["entity_id"] == actuator]

        if df_act.empty or len(df_act) < 30 or df_act["state"].nunique() == 1:
            logging.info(f"Skipping {actuator}")
            continue

        output_vector = df_act["state"]
        feature_list = sorted(list(set(act_list) - set([actuator])))
        feature_vector = df_act[feature_list]

        sensor_types = {sensor: classify_sensor_types(df_act, sensor, related_columns, sensor_model)
                        for sensor in feature_list}
        feature_vector = adjust_sensor_weights(feature_vector, sensor_types)

        X_train, X_test, y_train, y_test = train_test_split(feature_vector, output_vector, test_size=0.3)

        train_all_classifiers(
            model_types,
            actuator,
            X_train,
            X_test,
            y_train,
            y_test,
            None,
            metrics_matrix,
            feature_list,
        )

    save_metrics(metrics_matrix)
    logging.info("Completed!")
