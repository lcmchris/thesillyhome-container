import os
import pandas as pd
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import precision_recall_curve, accuracy_score, precision_score, recall_score, auc
import logging
import matplotlib.pyplot as plt

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config

def save_visual_tree(model, actuator, feature_vector):
    """
    Save a visual representation of a decision tree.
    """
    plt.figure(figsize=(12, 12))
    plot_tree(model, fontsize=10, feature_names=feature_vector, max_depth=5)
    plt.savefig(f"/thesillyhome_src/frontend/static/data/{actuator}_tree.png")
    plt.close()

def to_labels(pos_probs, threshold):
    """
    Apply a threshold to positive probabilities to create binary labels.
    """
    return (pos_probs >= threshold).astype("int")

def optimization_function(precision, recall):
    """
    Optimize the F-score using precision and recall.
    """
    epsilon = 0.01
    optimizer = (2 * precision * recall) / (1 / 5 * precision + recall + epsilon)
    ix = np.argmax(optimizer)
    return ix, optimizer

def train_all_actuator_models():
    """
    Train models for each actuator using the dataset.
    """
    actuators = tsh_config.actuators

    df_act_states = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl")
    df_act_states = df_act_states.reset_index(drop=True)

    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

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

    metrics_matrix = []

    for actuator in actuators:
        logging.info(f"Training model for {actuator}")

        df_act = df_act_states[df_act_states["entity_id"] == actuator]

        if df_act.empty or len(df_act) < 30 or df_act["state"].nunique() == 1:
            logging.info(f"Insufficient data for {actuator}, skipping.")
            continue

        output_vector = df_act["state"]

        cur_act_list = [feature for feature in act_list if feature.startswith(actuator)]
        feature_list = sorted(list(set(act_list) - set(cur_act_list)))
        feature_vector = df_act[feature_list]

        X = feature_vector
        y = output_vector

        synthetic_data = generate_synthetic_data(X, y, proportion=0.4)
        X = pd.concat([X, synthetic_data["X"]])
        y = pd.concat([y, synthetic_data["y"]])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

        sample_weight = np.ones(len(X_train))
        sample_weight[: int(len(sample_weight) * 0.2)] = 3

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

    save_metrics(metrics_matrix)
    logging.info("Completed training all models.")

def generate_synthetic_data(X, y, proportion=0.4):
    """
    Generate synthetic data to reduce overfitting and add diversity.
    """
    num_samples = int(len(X) * proportion)
    synthetic_X = X.sample(num_samples, replace=True)
    synthetic_y = y.sample(num_samples, replace=True)
    return {"X": synthetic_X, "y": synthetic_y}

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
    logging.info(f"---Training samples = {len(y_train)}")

    model_directory = f"{tsh_config.data_dir}/model/{actuator}"
    os.makedirs(model_directory, exist_ok=True)

    best_model = 0
    for model_name, model_vars in model_types.items():
        logging.info(f"---Running training for {model_name}")

        model = model_vars["classifier"](**model_vars["model_kwargs"])
        try:
            model.fit(X_train, y_train, sample_weight=sample_weight)
        except Exception as e:
            logging.warning(f"Training failed for {model_name} on {actuator}: {e}")
            continue

        if model_name == "DecisionTreeClassifier":
            save_visual_tree(model, actuator, feature_list)

        y_pred_proba = model.predict_proba(X_test)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)

        ix, optimizer = optimization_function(precision, recall)

        y_pred_best = to_labels(y_pred_proba, thresholds[ix])

        metrics = {
            "actuator": actuator,
            "classifier_name": model_name,
            "accuracy": accuracy_score(y_test, y_pred_best),
            "precision": precision_score(y_test, y_pred_best),
            "recall": recall_score(y_test, y_pred_best),
            "AUC": auc(recall, precision),
            "best_thresh": thresholds[ix],
            "best_optimizer": optimizer[ix],
            "model_enabled": optimizer[ix] > 0.7,
        }

        metrics_matrix.append(metrics)

        if optimizer[ix] > best_model:
            best_model = optimizer[ix]
            with open(f"{model_directory}/best_model.pkl", "wb") as f:
                pickle.dump(model, f)

def save_metrics(metrics_matrix):
    """
    Save metrics to disk.
    """
    metrics_df = pd.DataFrame(metrics_matrix)
    metrics_df.to_pickle(f"/thesillyhome_src/data/model/metrics.pkl")
    metrics_df.to_json(
        f"/thesillyhome_src/frontend/static/data/metrics_matrix.json",
        orient="records",
    )

if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        filename="/thesillyhome_src/log/thesillyhome.log",
        encoding="utf-8",
        level=logging.INFO,
        format=FORMAT,
    )
    train_all_actuator_models()
