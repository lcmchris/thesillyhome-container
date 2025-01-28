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

# Definiere bekannte Domains und Kategorien
domains_to_columns = {
    "light": "light",
    "switch": "light",
    "sensor": "sensor",
    "binary_sensor": "sensor",
    "input_boolean": "helper",
    "input_number": "helper",
    "input_text": "helper",
    "input_select": "helper",
    "input_datetime": "helper",
    "input_button": "helper",
    "cover": "cover",
    "media_player": "media_player",
    "person": "person",
    "sun": "sun",
    "temperature": "temperature",
    "humidity": "humidity",
    "illuminance": "illuminance",
    "current": "current",
    "power": "power",
    "energy": "energy",
    "volume": "volume",
    "pressure": "pressure",
    "voltage": "voltage",
    "lux": "lux",
}

def train_sensor_type_model(df, sensor_column, related_columns):
    """Trainiert ein Modell, um Sensoren basierend auf Spalten wie Licht oder Temperatur zu klassifizieren."""
    X = df[related_columns]
    y = df[sensor_column].apply(lambda x: "door" if "door" in x else "window" if "window" in x else "other")
    model = DecisionTreeClassifier(max_depth=5)
    model.fit(X, y)
    return model

def adjust_sensor_weights(X_train, sensor_types):
    """Passt die Gewichtung von Sensorwerten basierend auf deren Typ (z. B. Tür, Fenster) an."""
    for sensor, sensor_type in sensor_types.items():
        if sensor in X_train.columns:
            if sensor_type == "door":
                X_train[sensor] *= 2
            elif sensor_type == "window":
                X_train[sensor] *= 0.5
    return X_train

def classify_sensor_types(df, sensor_column, related_columns, model):
    """Klassifiziert Sensoren basierend auf den bereitgestellten Daten."""
    X = df[related_columns]
    return model.predict(X)

def train_all_actuator_models():
    """Trainiert Modelle für alle Aktoren basierend auf den verfügbaren Daten."""
    actuators = tsh_config.actuators
    df_act_states = pd.read_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl").reset_index(drop=True)
    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

    # Definiere Modeltypen und Parameter
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

    # Pivotiere Daten aus der Datenbankabfrage
    df_pivoted = df_act_states.pivot(index="state_id", columns="entity_id", values="state")

    # Dynamische Spaltenerstellung
    related_columns = []
    for domain, category in domains_to_columns.items():
        matching_columns = [col for col in df_pivoted.columns if domain in col]
        if matching_columns:
            related_columns.extend(matching_columns)
        else:
            logging.warning(f"No related columns found for domain '{domain}'.")

    # Fehlende Kategorien hinzufügen, falls nicht vorhanden
    missing_columns = [domain for domain in domains_to_columns if domain not in related_columns]
    if missing_columns:
        logging.warning(f"Missing columns for domains: {missing_columns}. Adding placeholders.")
        for col in missing_columns:
            df_pivoted[col] = 0  # Platzhalter-Werte
        related_columns.extend(missing_columns)

    # Debugging: Protokolliere die gefundenen Spalten
    logging.info(f"Identified related columns: {related_columns}")

    # Verarbeite und trainiere Modelle
    metrics_matrix = []
    sensor_column = "entity_id"
    sensor_model = train_sensor_type_model(df_pivoted, sensor_column, related_columns)

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

def train_all_classifiers(model_types, actuator, X_train, X_test, y_train, y_test, sample_weight, metrics_matrix, feature_list):
    """Trainiert und bewertet alle definierten Modelle."""
    best_model_score = 0
    for model_name, model_info in model_types.items():
        model = model_info["classifier"](**model_info["model_kwargs"])
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions, zero_division=0)
        recall = recall_score(y_test, predictions, zero_division=0)

        metrics_matrix.append({
            "actuator": actuator,
            "model": model_name,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
        })

        if accuracy > best_model_score:
            best_model_score = accuracy
            save_best_model(model, actuator)

def save_metrics(metrics_matrix):
    """Speichert die Metriken in einer Datei."""
    metrics_df = pd.DataFrame(metrics_matrix)
    metrics_df.to_csv(f"{tsh_config.data_dir}/metrics.csv", index=False)
    logging.info("Metrics saved.")

def save_best_model(model, actuator):
    """Speichert das beste Modell für einen Aktor."""
    filepath = f"{tsh_config.data_dir}/model/{actuator}_best_model.pkl"
    with open(filepath, "wb") as f:
        pickle.dump(model, f)
    logging.info(f"Saved best model for {actuator} at {filepath}.")
