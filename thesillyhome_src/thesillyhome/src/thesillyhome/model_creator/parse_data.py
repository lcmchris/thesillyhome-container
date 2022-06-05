# Library imports
from pandas.core.frame import DataFrame
import pandas as pd
import numpy as np
import copy
from joblib import Parallel, delayed
import tqdm
from tqdm import tqdm
import numpy as np
from multiprocessing import cpu_count

# Local application imports
from thesillyhome.model_creator.home import homedb
import thesillyhome.model_creator.read_config_json as tsh_config


def parallelize_dataframe(df1, df2, devices, func):
    num_processes = cpu_count()
    df_split = np.array_split(df1, num_processes)

    with tqdm(total=df1.shape[0]) as pbar:
        df_output = pd.concat(
            Parallel(n_jobs=-1, prefer="threads")(
                delayed(func)(split, df2, devices, pbar) for split in df_split
            )
        )
    return df_output


def add_device_states(df_output: pd.DataFrame, df_states: pd.DataFrame, devices, pbar):

    for index, row in df_output.iterrows():

        # Add last_state non-float onto dataframe as trigger
        last_device_state = df_states[
            (df_states["entity_id"].isin(devices))
            & (df_states["entity_id"] != row["entity_id"])
            & (df_states["last_changed"] < row["last_changed"])
            & ~(df_states["entity_id"].isin(tsh_config.float_sensors))
        ]
        if not last_device_state.empty:
            df_output.loc[
                index, "last_state"
            ] = f"{last_device_state['entity_id'].iloc[0]}_{last_device_state['state'].iloc[0]}"
        else:
            df_output.loc[index, "last_state"] = np.NaN

        last_current_device_state = df_states[
            (df_states["entity_id"] == row["entity_id"])
            & (df_states["last_changed"] < row["last_changed"])
        ]

        # Value actual state changes more!
        if not last_current_device_state.empty:
            if last_current_device_state["state"].iloc[0] == row["state"]:
                df_output.loc[index, "duplicate"] = 1
            else:
                df_output.loc[index, "duplicate"] = 3
        else:
            df_output.loc[index, "duplicate"] = 3

        # Add device states to dataframe as columns
        for device in devices:
            previous_device_state = df_states[
                (df_states["entity_id"] == device)
                & (df_states["last_changed"] < row["last_changed"])
            ]

            if not previous_device_state.empty:
                df_output.loc[index, device] = previous_device_state["state"].iloc[0]
            else:
                if device in tsh_config.float_sensors:
                    df_output.loc[index, device] = 0
                else:
                    df_output.loc[index, device] = "off"
        pbar.update(1)
    return df_output


# Hot encoding for all features
def one_hot_encoder(df: DataFrame, column: str) -> DataFrame:
    one_hot = pd.get_dummies(df[column], prefix=column)
    df = df.drop(column, axis=1)
    df = df.join(one_hot)
    return df


def convert_unavailabe(df: DataFrame) -> DataFrame:
    """
    The fact is if a device such as a light bulb is powered off,
    After a timeframe (availability_timeout), it is set to the 'unavailable' status

    ['entity_id','states']
    """
    df["state"] = np.where(
        (df["entity_id"].isin(tsh_config.float_sensors))
        & (df["state"].isin([np.NaN, "unknown", "", "unavailable", None])),
        0,
        df["state"],
    )
    df["state"] = np.where(
        (~df["entity_id"].isin(tsh_config.float_sensors))
        & (df["state"].isin([np.NaN, "unknown", "", "unavailable", None])),
        "off",
        df["state"],
    )
    return df


def parse_data_from_db(actuators: list, sensors: list):
    """
    Our data base currently stores by events.
    To create a valid ML classification case, we will parse all last
    sensor states for each actuator event and append it to the dataframe.
    """

    print("Reading from homedb...")
    df_all = homedb().get_data()
    df_all = convert_unavailabe(df_all)
    assert ~df_all["state"].isnull().values.any(), df_all[df_all["state"].isnull()]

    print("Add previous state...")
    devices = actuators + sensors
    df_states = df_all[df_all["entity_id"].isin(devices)]
    df_act_states = df_all[df_all["entity_id"].isin(actuators)]

    df_output = copy.deepcopy(df_act_states)

    print("Start parallelization processing...")

    df_output = parallelize_dataframe(df_output, df_states, devices, add_device_states)

    """
    Code to add one hot encoding for date time.
    This will help give features for time of day and day of the week.
    """
    df_output["hour"] = df_output["last_changed"].dt.hour
    df_output["weekday"] = df_output["last_changed"].dt.date.apply(
        lambda x: x.weekday()
    )
    df_output = df_output.drop(columns=["last_changed"])

    output_list = tsh_config.output_list.copy()
    output_list.append("duplicate")
    feature_list = sorted(list(set(df_output.columns) - set(output_list)))

    float_sensors = tsh_config.float_sensors
    for feature in feature_list:
        # For float sensors, these are already in Int format so no encoding.
        if feature not in float_sensors:
            df_output = one_hot_encoder(df_output, feature)

    # Remove some empty entity_id rows
    df_output = df_output[df_output["entity_id"] != ""]

    assert ~df_output.isnull().values.any(), df_output[
        df_output["sensor.corridor_entrance_sensor_illuminance_lux"].isnull()
    ]
    assert ~df_output.isin([np.inf, -np.inf, np.nan]).values.any()

    df_output.to_csv(
        f"{tsh_config.data_dir}/parsed/act_states.csv", index=True, index_label="index"
    )
