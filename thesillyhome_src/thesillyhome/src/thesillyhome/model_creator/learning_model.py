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
    related_columns = ["temperature", "light"]  # Passe das an die relevanten Spalten an

    # Debugging: Print all columns of df_act_states
    print("Available columns in df_act_states:", df_act_states.columns)

    # Verwende 'entity_id' als Fallback für die Sensorspalte
    sensor_column = "entity_id"

    # Trainiere das Sensor-Typ-Modell
    sensor_model = train_sensor_type_model(df_act_states, sensor_column, related_columns)

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
