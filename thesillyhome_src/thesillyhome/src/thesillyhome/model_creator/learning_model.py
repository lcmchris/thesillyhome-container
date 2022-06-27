# Library imports
import os
import subprocess
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score
import pickle
import logging
import json
import matplotlib.pyplot as plt

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config


def save_visual_tree(model_tree, actuator, model_name_version):
    # plot tree
    plt.figure(figsize=(12, 12))  # set plot size (denoted in inches)
    plot_tree(model_tree, fontsize=10)
    plt.savefig(f"{tsh_config.data_dir}/model/{model_name_version}/{actuator}_tree.png")


def train_model(model_name_version):
    """
    Train models for each actuator
    """

    actuators = tsh_config.actuators

    df_act_states = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl")
    df_act_states = df_act_states.reset_index(drop=True)

    # Generate feature and output vectors from act states.
    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

    # Adding metrics matrix
    metrics_matrix = []

    for actuator in actuators:
        logging.info(f"Training model for {actuator}")

        df_act = df_act_states[df_act_states["entity_id"] == actuator]

        if df_act.empty:
            logging.info(f"No cases found for {actuator}")
            continue

        """
        Setting output and feature vector
        """
        output_vector = df_act["state"]

        # the actuators feature state should not affect the model and also the duplicate column
        cur_act_list = []
        for feature in act_list:
            if feature.startswith(actuator):
                cur_act_list.append(feature)
        feature_list = sorted(list(set(act_list) - set(cur_act_list)))
        feature_vector = df_act[feature_list]

        # Split into random training and test set
        X = feature_vector
        y = output_vector
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=170
        )

        # # Weighting more recent observations more. 3 times if in top 50 percent
        sample_weight = np.ones(len(X_train))
        sample_weight[: int(len(sample_weight) * 0.2)] = 3

        # Weighting duplicates less
        sample_weight = sample_weight * X_train["duplicate"]
        X_train = X_train.drop(columns="duplicate")
        X_test = X_test.drop(columns="duplicate")
        y_train = y_train.drop(columns="duplicate")
        y_test = y_test.drop(columns="duplicate")

        model_tree = DecisionTreeClassifier(random_state=99)
        model_tree.fit(X_train, y_train, sample_weight=sample_weight)

        # Visualization of tress:
        # tree_to_code(model_tree, feature_list)
        save_visual_tree(model_tree, actuator, model_name_version)

        # Get predictions of model
        y_tree_predictions = model_tree.predict(X_test)

        # Extract predictions for each output variable and calculate accuracy and f1 score
        accuracy = accuracy_score(y_test, y_tree_predictions)
        precision = precision_score(y_test, y_tree_predictions)
        recall = recall_score(y_test, y_tree_predictions)

        metrics_json = {}
        metrics_json["actuator"] = actuator
        metrics_json["accuracy"] = accuracy
        metrics_json["precision"] = precision
        metrics_json["recall"] = recall

        metrics_matrix.append(metrics_json)

        logging.info(
            f"{actuator} accuracy score: {accuracy * 100}" + "\n"
            f"{actuator} precision score: {precision * 100}" + "\n"
            f"{actuator} recall score: {recall * 100}"
        )

        # Save model to disk
        model_directory = f"{tsh_config.data_dir}/model/{model_name_version}"
        os.makedirs(model_directory, exist_ok=True)

        filename = open(f"{model_directory}/{actuator}.pickle", "wb")
        pickle.dump(model_tree, filename)

    with open(
        f"{tsh_config.data_dir}/model/{model_name_version}/metrics_matrix.json", "w"
    ) as fp:
        json.dump(metrics_matrix, fp)
    logging.info("Completed!")
