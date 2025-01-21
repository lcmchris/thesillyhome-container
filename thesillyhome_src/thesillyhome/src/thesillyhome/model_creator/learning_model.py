# Library imports
from cmath import exp
import os
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import precision_recall_curve

import sys

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, auc
import pickle
import logging
import matplotlib.pyplot as plt

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config


def save_visual_tree(model, actuator, feature_vector):
    # plot tree
    plt.figure(figsize=(12, 12))  # set plot size (denoted in inches)
    plot_tree(model, fontsize=10, feature_names=feature_vector, max_depth=5)
    plt.savefig(f"/thesillyhome_src/frontend/static/data/{actuator}_tree.png")
    plt.close()


# apply threshold to positive probabilities to create labels
def to_labels(pos_probs, threshold):
    return (pos_probs >= threshold).astype("int")


def optimization_fucntion(precision, recall):
    # convert to f score
    epsilon = 0.01
    optimizer = (2 * precision * recall) / (1 / 5 * precision + recall + epsilon)

    # locate the index of the largest f score
    ix = np.argmax(optimizer)
    return ix, optimizer


def train_all_actuator_models():
    """
    Train models for each actuator
    """
    actuators = tsh_config.actuators

    df_act_states = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl")
    df_act_states = df_act_states.reset_index(drop=True)

    # Generate feature and output vectors from act states.
    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

    # Initialization
    model_types = {
        "DecisionTreeClassifier": {
            "classifier": DecisionTreeClassifier,
            "model_kwargs": {},
        },
        "LogisticRegression": {
            "classifier": LogisticRegression,
            "model_kwargs": {"max_iter": 10000},
        },
        "RandomForestClassifier": {
            "classifier": RandomForestClassifier,
            "model_kwargs": {},
        },
        "SVMClassifier": {
            "classifier": SVC,
            "model_kwargs": {"probability": True},
        },
    }

    # Adding metrics matrix
    metrics_matrix = []

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
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

        # # Weighting more recent observations more. 3 times if in top 50 percent
        sample_weight = np.ones(len(X_train))
        sample_weight[: int(len(sample_weight) * 0.2)] = 3

        # Weighting duplicates less
        sample_weight = sample_weight * X_train["duplicate"]
        X_train = X_train.drop(columns="duplicate")
        X_test = X_test.drop(columns="duplicate")
        y_train = y_train.drop(columns="duplicate")
        y_test = y_test.drop(columns="duplicate")

        train_all_classifiers(
            model_types,
            actuator,
            X_train,
            X_test,
            y_train,
            y_test,
            sample_weight,
            metrics_matrix,
            feature_list,
        )

    df_metrics_matrix = pd.DataFrame(metrics_matrix)
    df_metrics_matrix.to_pickle(f"/thesillyhome_src/data/model/metrics.pkl")

    try:
        best_metrics_matrix = df_metrics_matrix.fillna(0)
        best_metrics_matrix = df_metrics_matrix.sort_values(
            "best_optimizer", ascending=False
        ).drop_duplicates(subset=["actuator"], keep="first")
    except:
        logging.warning("No metrics.")

    best_metrics_matrix.to_json(
        "/thesillyhome_src/frontend/static/data/metrics_matrix.json", orient="records"
    )

    logging.info("Completed!")


def train_all_classifiers(
    model_types,
    actuator,
    X_train,
    X_test,
    y_train,
    y_test,
    sample_weight,
    metrics_matrix,
    feature_list,
):
    """ """
    logging.info(f"---Training samples = {len(y_train)}")

    model_directory = f"{tsh_config.data_dir}/model/{actuator}"
    os.makedirs(model_directory, exist_ok=True)

    best_model = 0
    for model_name, model_vars in model_types.items():
        logging.info(f"---Running training for {model_name}")
        logging.info(f"-----Model Kwargs = {model_vars['model_kwargs']}")

        model = model_vars["classifier"](**model_vars["model_kwargs"])
        try:
            model.fit(X_train, y_train, sample_weight=sample_weight)
        except:
            continue

        # Visualization of tress:
        if model_name == "DecisionTreeClassifier":
            save_visual_tree(model, actuator, feature_list)

        # Get predictions of model
        y_predictions_proba = model.predict_proba(X_test)

        # keep probabilities for the positive outcome only
        y_predictions_proba = y_predictions_proba[:, 1]

        # calculate roc curves
        precision, recall, thresholds = precision_recall_curve(
            y_test, y_predictions_proba
        )

        ix, optimizer = optimization_fucntion(precision, recall)
        auc_ = auc(recall, precision)

        # plot the roc curve for the model
        plt.plot(precision, recall, label=model_name, markevery=None)
        plt.scatter(precision[ix], recall[ix], marker="o", label=f"{model_name}")

        # axis labels
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.legend()
        # show the plot

        y_predictions_best = to_labels(y_predictions_proba, thresholds[ix])

        # # Extract predictions for each output variable and calculate accuracy and f1 score
        accuracy_best = accuracy_score(y_test, y_predictions_best)
        precision_best = precision_score(y_test, y_predictions_best)
        recall_best = recall_score(y_test, y_predictions_best)

        metrics_json = {}
        metrics_json["actuator"] = actuator
        metrics_json["classifier_name"] = model_name
        metrics_json["accuracy"] = accuracy_best
        metrics_json["precision"] = precision_best
        metrics_json["recall"] = recall_best
        metrics_json["AUC"] = auc_
        metrics_json["best_thresh"] = thresholds[ix]
        metrics_json["best_optimizer"] = optimizer[ix]
        metrics_json["model_enabled"] = False

        metrics_matrix.append(metrics_json)

        # Save model to disk
        filename = open(f"{model_directory}/{model_name}.pkl", "wb")
        pickle.dump(model, filename)

        # Save model to disk
        if optimizer[ix] > best_model:
            if precision_best > 0.7 and not tsh_config.startup_disable_all:
                metrics_json["model_enabled"] = True
            best_model = optimizer[ix]
            filename = open(f"{model_directory}/best_model.pkl", "wb")
            pickle.dump(model, filename)

    # plot
    plt.plot(
        [0, 1],
        [y_train.sum() / len(y_train), y_train.sum() / len(y_train)],
        linestyle="--",
        label="No Skill",
    )
    plt.savefig(f"{tsh_config.data_dir}/model/{actuator}/precision_recall.jpg")
    plt.savefig(
        f"/thesillyhome_src/frontend/static/data/{actuator}_precision_recall.png"
    )
    plt.close()


if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        filename="/thesillyhome_src/log/thesillyhome.log",
        encoding="utf-8",
        level=logging.INFO,
        format=FORMAT,
    )
    root = logging.getLogger()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    train_all_actuator_models()
