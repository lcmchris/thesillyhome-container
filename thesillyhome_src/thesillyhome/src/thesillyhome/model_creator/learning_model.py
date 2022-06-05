# Library imports
import os
import subprocess
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_graphviz
import numpy as np
from sklearn.metrics import accuracy_score
import pickle

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config


def visualize_tree(tree, actuators, feature_names, model_name_version):
    """Create tree png using graphviz.
    Args
    ----
    tree -- scikit-learn DecsisionTree.
    feature_names -- list of feature names.
    """
    with open(
        f"{tsh_config.data_dir}/model/{model_name_version}/{actuator}.dot", "w"
    ) as f:
        export_graphviz(tree, out_file=f, feature_names=feature_names)

    command = [
        "dot",
        "-Tpng",
        f"{tsh_config.data_dir}/model/{model_name_version}/{actuator}.dot",
        "-o",
        f"{tsh_config.data_dir}/model/{model_name_version}/{actuator}.png",
    ]
    try:
        subprocess.check_call(command)
        os.remove(f"{tsh_config.data_dir}/model/{model_name_version}/{actuator}.dot")
    except:
        exit("Could not run dot, ie graphviz, to produce visualization")


def train_model(actuators: list, model_name_version):

    # Generate feature and output vectors from act states.
    df_act_states = pd.read_csv(
        f"{tsh_config.data_dir}/parsed/act_states.csv", index_col=False
    ).drop(columns=["index"])

    df_act_states = df_act_states.replace([np.inf, -np.inf], np.nan)
    df_act_states = df_act_states.fillna(999)

    output_list = tsh_config.output_list.copy()
    act_list = list(set(df_act_states.columns) - set(output_list))

    for actuator in actuators:
        print(f"Training model for {actuator}")

        df_act = df_act_states[df_act_states["entity_id"] == actuator]
        df_act = df_act.reset_index(drop=True)

        if df_act.empty:
            print(f"No cases found for {actuator}")
            continue
        output_vector = np.where(df_act["state"] == "on", 1, 0)

        # the actuators state should not affect the model
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
        # sample_weight = np.ones(len(X_train))
        # sample_weight[: int(len(sample_weight) * 0.2)] = 3

        # Weighting duplicates less
        sample_weight = X_train["duplicate"]

        X_train = X_train.drop(columns="duplicate")
        X_test = X_test.drop(columns="duplicate")

        model_tree = DecisionTreeClassifier(random_state=99)
        model_tree.fit(X_train, y_train, sample_weight=sample_weight)

        feature_list.remove("duplicate")

        # Visualization of tress:
        # tree_to_code(model_tree, feature_list)
        # visualize_tree(model_tree, feature_list)

        # Get predictions of model
        y_tree_predictions = model_tree.predict(X_test)

        # Extract predictions for each output variable and calculate accuracy and f1 score
        print(
            f"{actuator} accuracy score: {accuracy_score(y_test, y_tree_predictions) * 100}"
        )

        # Save model to disk
        model_directory = f"{tsh_config.data_dir}/model/{model_name_version}"
        os.makedirs(model_directory, exist_ok=True)

        filename = open(f"{model_directory}/{actuator}.pickle", "wb")
        pickle.dump(model_tree, filename)
    print("Completed!")
