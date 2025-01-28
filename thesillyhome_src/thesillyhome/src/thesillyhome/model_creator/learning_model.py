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
    feature_names = feature_vector.columns.tolist()  # Extrahiert Spaltennamen
    plt.figure(figsize=(12, 12))
    plot_tree(model, fontsize=10, feature_names=feature_names, max_depth=7)
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


def train_all_actuator_models():
    """Trains models for each actuator."""
    actuators = tsh_config.actuators
    df_act_states = pd.read_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl").reset_index(drop=True)

    # Sort data by ascending timestamps
    df_act_states.sort_values(by="last_updated", ascending=True, inplace=True)

    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

    model_types = {
        "DecisionTreeClassifier": {
            "classifier": DecisionTreeClassifier,
            "model_kwargs": {
                "max_depth": 7,
                "min_samples_split": 5,
                "min_samples_leaf": 3,
            },
        },
        "LogisticRegression": {
            "classifier": LogisticRegression,
            "model_kwargs": {
                "max_iter": 10000,
                "C": 0.5,
            },
        },
        "RandomForestClassifier": {
            "classifier": RandomForestClassifier,
            "model_kwargs": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 3,
            },
        },
        "SVMClassifier": {
            "classifier": SVC,
            "model_kwargs": {
                "probability": True,
                "C": 0.5,
            },
        },
    }

    metrics_matrix = []

    for actuator in actuators:
        logging.info(f"Training model for {actuator}")
        df_act = df_act_states[df_act_states["entity_id"] == actuator]

        if df_act.empty:
            logging.info(f"No cases found for {actuator}")
            continue

        if len(df_act) < 60:
            logging.info("Samples less than 60. Skipping")
            continue

        if df_act["state"].nunique() == 1:
            logging.info(f"All cases for {actuator} have the same state. Skipping")
            continue

        output_vector = df_act["state"]
        cur_act_list = [feature for feature in act_list if feature.startswith(actuator)]
        feature_list = sorted(list(set(act_list) - set(cur_act_list)))
        feature_vector = df_act[feature_list]

        # Generate weights for ASC data
        weights = np.linspace(0.3, 0.7, len(df_act))
        df_act["weight"] = weights

        X_train, X_test, y_train, y_test, weights_train, weights_test = train_test_split(
            feature_vector, output_vector, df_act["weight"], test_size=0.4
        )

        if "duplicate" in X_train.columns:
            weights_train *= X_train["duplicate"]
            X_train = X_train.drop(columns="duplicate")
            X_test = X_test.drop(columns="duplicate")

        train_all_classifiers(
            model_types,
            actuator,
            X_train,
            X_test,
            y_train,
            y_test,
            weights_train,
            metrics_matrix,
            feature_list,
        )

    save_metrics(metrics_matrix)
    logging.info("Completed!")


def train_all_classifiers(model_types, actuator, X_train, X_test, y_train, y_test, sample_weight, metrics_matrix, feature_list):
    logging.info(f"---Training samples = {len(y_train)}")

    model_directory = f"{tsh_config.data_dir}/model/{actuator}"
    os.makedirs(model_directory, exist_ok=True)

    best_model = 0
    for model_name, model_vars in model_types.items():
        logging.info(f"---Running training for {model_name}")

        # Zielwerte in numerische Werte konvertieren
        y_train_numeric = y_train.replace({"on": 1, "off": 0})
        y_test_numeric = y_test.replace({"on": 1, "off": 0})

        model = model_vars["classifier"](**model_vars["model_kwargs"])
        try:
            model.fit(X_train, y_train_numeric, sample_weight=sample_weight)
        except Exception as e:
            logging.error(f"Training failed for {model_name} on {actuator}: {e}")
            continue

        if model_name == "DecisionTreeClassifier":
            save_visual_tree(model, actuator, feature_list)

        if len(model.classes_) > 1:
            y_predictions_proba = model.predict_proba(X_test)[:, 1]
        else:
            logging.warning(f"Skipping {actuator} with {model_name}: only one class present.")
            continue

        precision, recall, thresholds = precision_recall_curve(y_test_numeric, y_predictions_proba)

        ix, optimizer = optimization_function(precision, recall)
        auc_ = auc(recall, precision)

        y_predictions_best = to_labels(y_predictions_proba, thresholds[ix])

        metrics_json = {
            "actuator": actuator,
            "classifier_name": model_name,
            "accuracy": accuracy_score(y_test_numeric, y_predictions_best),
            "precision": precision_score(y_test_numeric, y_predictions_best),
            "recall": recall_score(y_test_numeric, y_predictions_best),
            "AUC": auc_,
            "best_thresh": thresholds[ix],
            "best_optimizer": optimizer[ix],
            "model_enabled": False,
        }

        metrics_matrix.append(metrics_json)

        if optimizer[ix] > best_model and metrics_json["precision"] > 0.7:
            metrics_json["model_enabled"] = True
            best_model = optimizer[ix]
            save_model(model, f"{model_directory}/best_model.pkl")

        save_model(model, f"{model_directory}/{model_name}.pkl")

    save_plots(actuator, y_train_numeric)


def save_model(model, filepath):
    with open(filepath, "wb") as file:
        pickle.dump(model, file)


def save_plots(actuator, y_train):
    plt.plot(
        [0, 1],
        [y_train.sum() / len(y_train), y_train.sum() / len(y_train)],
        linestyle="--",
        label="No Skill",
    )
    plt.savefig(f"/thesillyhome_src/frontend/static/data/{actuator}_precision_recall.png")
    plt.close()


def save_metrics(metrics_matrix):
    df_metrics_matrix = pd.DataFrame(metrics_matrix)
    df_metrics_matrix.to_pickle(f"/thesillyhome_src/data/model/metrics.pkl")

    try:
        best_metrics_matrix = df_metrics_matrix.fillna(0).sort_values(
            "best_optimizer", ascending=False
        ).drop_duplicates(subset=["actuator"], keep="first")
    except Exception as e:
        logging.warning(f"No metrics available: {e}")
        return

    metrics_path = "/thesillyhome_src/frontend/static/data/metrics_matrix.json"
    if not os.path.exists(metrics_path):
        with open(metrics_path, "w") as f:
            f.write("[]")

    best_metrics_matrix.to_json(metrics_path, orient="records")


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
