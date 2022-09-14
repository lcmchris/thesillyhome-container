# Library imports
from datetime import datetime
import string
import mysql.connector
import psycopg2
import pandas as pd
import os.path
import os
import logging
import uuid
from sqlalchemy import create_engine

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config


"""
  Get data from DB and store locally
"""


class homedb:
    def __init__(self):
        self.host = tsh_config.db_host
        self.port = tsh_config.db_port
        self.username = tsh_config.db_username
        self.password = tsh_config.db_password
        self.database = tsh_config.db_database
        self.db_type = tsh_config.db_type
        self.share_data = tsh_config.share_data
        self.from_cache = False
        self.mydb = self.connect_internal_db()
        self.extdb = self.connect_external_db()
        self.user_id = tsh_config.db_database + "_" + hex(uuid.getnode())

    def connect_internal_db(self):
        if not self.from_cache:
            if self.db_type == "postgres":
                mydb = create_engine(
                    f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
                    echo=False,
                )
            elif self.db_type == "mariadb":
                mydb = create_engine(
                    f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
                    echo=False,
                )
            else:
                raise Exception(f"Invalid DB type : {self.db_type}.")
            return mydb
        else:
            return None

    def connect_external_db(self):
        host = tsh_config.extdb_host
        port = tsh_config.extdb_port
        user = tsh_config.extdb_username
        password = tsh_config.extdb_password
        database = tsh_config.extdb_database
        extdb = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", echo=False
        )
        return extdb

    def get_data(self):
        logging.info("Getting data from internal homeassistant db")

        if self.from_cache:
            logging.info("Using cached all_states.pkl")
            return pd.read_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        logging.info("Executing query")

        query = f"SELECT \
                    state_id,\
                    entity_id  ,\
                    state  ,\
                    last_changed  ,\
                    last_updated  ,\
                    old_state_id \
                from states ORDER BY last_updated DESC;"
        with self.mydb.connect() as con:
            con = con.execution_options(stream_results=True)
            list_df = [
                df
                for df in pd.read_sql(
                    query,
                    con=con,
                    index_col="state_id",
                    parse_dates=["last_changed", "last_updated"],
                    chunksize=1000,
                )
            ]
            df_output = pd.concat(list_df)
        df_output.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        if self.share_data:
            logging.info("Uploading data to external db. *Thanks for sharing!*")
            self.upload_data(df_output)
        return df_output

    def upload_data(self, df: pd.DataFrame):
        last_update_time = self.get_user_info()
        df["user_id"] = self.user_id
        df = df[df["last_updated"] > last_update_time]
        if not df.empty:
            logging.info(df.shape)

            ## The Upload seems to be crazy slow
            # try:
            #     df.to_sql(
            #         name="states",
            #         con=self.extdb,
            #         if_exists="append",
            #         method="multi",
            #         chunksize=3000,
            #     )
            #     logging.info(f"Data uploaded.")
            # except:
            #     logging.warning(f"Duplicate Data found in db.")
            max_time = df["last_updated"].max()
            self.update_user(max_time)
        else:
            logging.info(f"Latest data already uploaded.")

    def get_user_info(self):
        # here we use the mac address as a dummy, this is used for now until an actual login system
        logging.info(f"Using MAC address as user_id {self.user_id}")

        query = f"SELECT \
                    last_update_time \
                from users where user_id = '{self.user_id}';"

        with self.extdb.begin() as connection:
            myresult = connection.execute(query).fetchall()

        if len(myresult) == 1:
            last_update_time = myresult[0][0]
            logging.info(
                f"User id {self.user_id} exists, last_updated : {last_update_time}"
            )
        else:
            # Add user if none
            logging.info(f"User id does not exist, creating new user: {self.user_id}")
            last_update_time = datetime(1900, 1, 1, 0, 0, 0, 0)
            query = f"CALL CreateUser ('{self.user_id}','{last_update_time}');"
            with self.extdb.begin() as connection:
                connection.execute(query)
        return last_update_time

    def update_user(self, c_time: datetime):
        logging.info(f"Updating user table with last_update_time {c_time} and config")
        query = f"CALL UpdateUser ('{self.user_id}','{c_time}','{tsh_config.options_json}');"

        with self.extdb.begin() as connection:
            connection.execute(query)
