import os
import sys
import pickle
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import precision_recall_curve, accuracy_score, precision_score, recall_score, auc
from sklearn.preprocessing import MinMaxScaler

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config

def save_visual_tree(model, actuator, feature_vector):
    """Saves a visual representation of a decision tree."""
    plt.figure(figsize=(12, 12))
    plot_tree(model, fontsize=10, feature_names=feature_vector, max_depth=7)
    plt.savefig(f"/thesillyhome_src/frontend/static/data/{actuator}_tree.png")
    plt.close()

def to_labels(pos_probs, threshold):
    """Converts probabilities to binary labels based on a threshold."""
    return (pos_probs >= threshold).astype("int")

def optimization_function(precision, recall):
    """Calculates the optimal threshold based on a custom optimization metric."""
    epsilon = 0.01
    optimizer = (2 * precision * recall) / (1 / 5 * precision + recall + epsilon)
    ix = np.argmax(optimizer)
    return ix, optimizer

def extract_sensor_behavior(df, sensor_column, related_columns, time_window=5):
    """
    Analyzes sensor behavior based on changes in related columns.
    :param df: DataFrame with sensor data.
    :param sensor_column: Name of the sensor to analyze.
    :param related_columns: List of related columns to check changes (e.g., temperature, light).
    :param time_window: Time window to analyze changes (in steps).
    :return: DataFrame with behavior analysis.
    """
    df_behavior = pd.DataFrame()
    for related in related_columns:
        df[f"{sensor_column}_change_in_{related}"] = df[related].diff(periods=time_window)
    return df

def classify_sensor_types(df, sensor_column, related_columns, model):
    """
    Classifies a sensor as door or window based on behavior.
    :param df: DataFrame with sensor data and behavior analysis.
    :param sensor_column: The sensor to classify.
    :param related_columns: Columns describing behavior (e.g., temperature, light changes).
    :param model: Pre-trained classification model (e.g., DecisionTreeClassifier).
    :return: Sensor classification ("door", "window", etc.).
    """
    X = df[related_columns]
    return model.predict(X)

def adjust_sensor_weights(X_train, sensor_types):
    """
    Adjusts the weights of specific sensors for training based on their types.
    :param X_train: Training dataset.
    :param sensor_types: Dictionary of sensor types ("door", "window").
    :return: Weighted training dataset.
    """
    for sensor, sensor_type in sensor_types.items():
        if sensor in X_train.columns:
            if sensor_type == "door":
                logging.info(f"Boosting weight for door sensor: {sensor}")
                X_train[sensor] *= 2
            elif sensor_type == "window":
                logging.info(f"Reducing weight for window sensor: {sensor}")
                X_train[sensor] *= 0.5
    return X_train

def train_sensor_type_model(df, sensor_column, related_columns):
    """
    Trains a model to classify sensors as doors or windows based on behavior.
    :param df: DataFrame with sensor data and behavior analysis.
    :param sensor_column: The sensor column to classify.
    :param related_columns: Columns describing behavior (e.g., temperature, light changes).
    :return: Trained classification model.
    """
    labels = []  # Provide manual labels for training ("door" or "window")
    for index, row in df.iterrows():
        if "door" in row[sensor_column]:  # Replace this with your own labeling logic
            labels.append("door")
        else:
            labels.append("window")
    model = DecisionTreeClassifier(max_depth=5)
    model.fit(df[related_columns], labels)
    return model

def train_all_actuator_models():
    """Trains models for each actuator."""
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
    related_columns = ["temperature", "light"]  # Adjust this based on available data

    # Train sensor type model
    sensor_model = train_sensor_type_model(df_act_states, "sensor_id", related_columns)

    for actuator in actuators:
        logging.info(f"Training model for {actuator}")
        df_act = df_act_states[df_act_states["entity_id"] == actuator]

        if df_act.empty:
            logging.info(f"No cases found for {actuator}")
            continue

        if len(df_act) < 30:
            logging.info("Samples less than 30. Skipping")
            continue

        if df_act["state"].nunique() == 1:
            logging.info(f"All cases for {actuator} have the same state. Skipping")
            continue

        output_vector = df_act["state"]
        feature_list = sorted(list(set(act_list) - set([actuator])))
        feature_vector = df_act[feature_list]

        # Classify sensor types
        sensor_types = {sensor: classify_sensor_types(df_act, sensor, related_columns, sensor_model)
                        for sensor in feature_list}

        # Adjust weights based on sensor types
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

if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        filename="/thesillyhome_src/log/thesillyhome.log",
        encoding="utf-8",
        level=logging.INFO,
        format=FORMAT,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(FORMAT))
    logging.getLogger().addHandler(handler)

    train_all_actuator_models()
