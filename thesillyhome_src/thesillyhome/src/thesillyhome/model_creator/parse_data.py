# Library imports
import pandas as pd
import numpy as np
import logging

# Local application imports
from thesillyhome.model_creator.home import homedb
from thesillyhome.model_creator.logger import add_logger
from thesillyhome.model_creator.config_checker import check_device_ids
import thesillyhome.model_creator.read_config_json as tsh_config


def get_current_states(df_output: pd.DataFrame) -> pd.DataFrame:
    """
    Returns pivoted frame of each state id desc
    """
    df_pivot = (
        df_output.reset_index()
        .pivot(index=["state_id"], columns=["entity_id"], values=["state"])
        .sort_values(by="state_id", ascending=False)
    )
    df_pivot.columns = df_pivot.columns.droplevel(0)
    df_pivot = df_pivot.fillna(method="bfill").fillna(method="ffill")
    return df_pivot


def add_duplicate(df_output: pd.DataFrame) -> pd.DataFrame:

    for entity in df_output["entity_id"].unique():
        df_filtered = df_output[df_output["entity_id"] == entity]
        df_shift = df_filtered.shift(-1)

        df_output.loc[df_output["entity_id"] == entity, "duplicate"] = np.where(
            df_filtered["state"] == df_shift["state"], 1, 3
        )

    return df_output


def one_hot_encoder(df: pd.DataFrame, column: str) -> pd.DataFrame:
    one_hot = pd.get_dummies(df[column], prefix=column)
    df = df.drop(column, axis=1)
    df = df.join(one_hot)
    return df


def convert_unavailabe(df: pd.DataFrame) -> pd.DataFrame:
    """
    The fact is if a device such as a light bulb is powered off,
    After a timeframe (availability_timeout), it is set to the 'unavailable' status

    ['entity_id','states']
    """
    conditions = [
        (df["entity_id"].isin(tsh_config.float_sensors))
        & (df["state"].isin([np.NaN, "unknown", "", "unavailable", None])),
        (~df["entity_id"].isin(tsh_config.float_sensors))
        & (df["state"].isin([np.NaN, "unknown", "", "unavailable", None])),
    ]

    choices = [0, "off"]
    return np.select(conditions, choices, default=df["state"])


def parse_data_from_db():
    """
    Our data base currently stores by events.
    To create a valid ML classification case, we will parse all last
    sensor states for each actuator event and append it to the dataframe.
    """

    logging.info("Reading from homedb...")
    df_all = homedb().get_data()
    df_all = df_all[["entity_id", "state", "last_updated"]]

    check_device_ids(df_all["entity_id"].unique())
    logging.info(tsh_config.actuators)
    logging.info(tsh_config.sensors)

    df_all["state"] = convert_unavailabe(df_all)
    assert ~df_all["state"].isnull().values.any(), df_all[df_all["state"].isnull()]

    df_all = df_all[df_all["entity_id"].isin(tsh_config.devices)]

    logging.info("Add previous state...")
    df_act_states = df_all[df_all["entity_id"].isin(tsh_config.actuators)]

    logging.info("Start parallelization processing...")

    df_current_states = get_current_states(df_all)
    df_output = df_act_states.join(df_current_states, on="state_id")

    df_output = add_duplicate(df_output)

    """
    Code to add one hot encoding for date time.
    This will help give features for time of day and day of the week.
    """
    df_output["last_updated"] = pd.to_datetime(df_output["last_updated"])
    df_output["hour"] = df_output["last_updated"].dt.hour
    df_output["weekday"] = df_output["last_updated"].dt.date.apply(
        lambda x: x.weekday()
    )
    df_output = df_output.drop(columns=["last_updated"])

    """
    feature list extraction
    """
    output_list = tsh_config.output_list.copy()
    output_list.append("duplicate")
    feature_list = sorted(list(set(df_output.columns) - set(output_list)))

    """
    Hot encoding for all columns bar float_sensors which has int format
    """
    for feature in feature_list:
        if feature not in tsh_config.float_sensors:
            df_output = one_hot_encoder(df_output, feature)

    """
    Output and checks
    """
    df_output["state"] = np.where(df_output["state"] == "on", 1, 0)

    assert df_output[df_output["entity_id"] == ""].empty
    assert ~df_output.isnull().values.any()
    assert ~df_output.isin([np.inf, -np.inf, np.NaN]).values.any()

    dtype_dict = {}
    for col in list(df_output.columns):
        if col == "entity_id":
            dtype_dict[col] = "object"
        else:
            dtype_dict[col] = "int8"
    df_output = df_output.astype(dtype_dict)

    df_output.to_pickle(f"{tsh_config.data_dir}/parsed/act_states.pkl")


if __name__ == "__main__":
    add_logger()
    parse_data_from_db()
