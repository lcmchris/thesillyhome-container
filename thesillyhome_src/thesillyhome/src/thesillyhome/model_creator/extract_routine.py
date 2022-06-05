# Library imports
import os
import pandas as pd
import numpy as np
# Local application imports
import pickle
from sklearn.tree import _tree



def tree_to_code(tree, feature_names):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]

    def recurse(node, depth):
        indent = "    " * depth
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            if tree_.children_left[node] < tree_.children_right[node]:
                print("{}if {} <= {}:".format(indent, name, np.round(threshold, 2)))
                recurse(tree_.children_left[node], depth + 1)
            else:
                print("{}if {} > {}".format(indent, name, np.round(threshold, 2)))
                recurse(tree_.children_right[node], depth + 1)
        else:
            print("{}return {}".format(indent, tree_.value[node]))

    recurse(0, 1)


if __name__ == "__main__":
    cur_dir = os.path.dirname(__file__)
    model_name = "test"
    output_list = ["entity_id", "state", "created"]
    df_act_states = pd.read_csv(
        f"/data/act_states.csv", index_col=False
    ).drop(columns=["index"])
    act_list = list(set(df_act_states.columns) - set(output_list))

    for actuator in configuration.actuators:
        # the actuators state should not affect the model
        cur_act_list = []
        for feature in act_list:
            if feature.startswith(actuator):
                cur_act_list.append(feature)
        feature_list = sorted(list(set(act_list) - set(cur_act_list)))
        filename = f"/data/model/{model_name}/{actuator}.pickle"
        if os.path.getsize(filename) > 0:
            print(f"\n{actuator}")
            hello = pickle.load(open(filename, "rb"))
            tree_to_code(hello, feature_list)
