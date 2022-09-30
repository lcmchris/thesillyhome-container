# Library imports
from datetime import datetime
import mysql.connector
import psycopg2
import pandas as pd
import os.path
import os
import logging
from sqlalchemy import create_engine
import bcrypt
import json

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
        self.valid_user = self.verify_username()

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

    def get_data(self) -> pd.DataFrame:
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
            try:
                self.upload_data(df_output)
            except:
                logging.warning("User info not saved.")
        return df_output

    def upload_data(self, df: pd.DataFrame):
        if self.valid_user is None:
            last_update_time = self.create_user()
        else:
            last_update_time = self.valid_user()

        df["user_id"] = tsh_config.username
        df = df[df["last_updated"] > last_update_time]
        if not df.empty:
            max_time = df["last_updated"].max()
            self.update_user(max_time)
        else:
            logging.info(f"Latest data already uploaded.")

    def update_user(self, c_time: datetime):
        logging.info(f"Updating user table with last_update_time {c_time} and config")
        options_json = json.dumps(
            {
                k: tsh_config.options[k]
                for k in set(list(tsh_config.keys())) - set(["ha_options", "password"])
            }
        )
        query = f"UPDATE thesillyhomedb.users \
            SET last_update_time = '{c_time}',\
            config = '{options_json}' \
            WHERE user_id = '{tsh_config.username}';"

        with self.extdb.begin() as connection:
            connection.execute(query)

    def verify_username(self):
        query = f"SELECT \
                    password, last_update_time \
                from users where user_id = '{tsh_config.username}';"
        with self.extdb.begin() as connection:
            myresult = connection.execute(query).fetchall()
        if len(myresult) == 1:
            found_pwd = myresult[0][0]
            if check_password(tsh_config.password, found_pwd):
                logging.info(
                    f"Username {tsh_config.username} exists, correct password. Proceeding..."
                )
                last_update_time = myresult[0][1]
                logging.info(f"Last updated time: {last_update_time}")
                return last_update_time
            else:
                raise ValueError(
                    f"User id {tsh_config.username} already exists. Please use a different username or try a different password."
                )
        elif len(myresult) == 0:
            return None

    def create_user(self):

        logging.info(
            f"Username {tsh_config.username} does not exist. Creating new user."
        )
        last_update_time = datetime(1900, 1, 1, 0, 0, 0, 0)
        logging.info(tsh_config.password)
        new_hashed_pwd = get_hashed_password(tsh_config.password).decode("utf-8")

        query = f"INSERT INTO thesillyhomedb.users (user_id,password,last_update_time) \
                VALUES ('{tsh_config.username}','{new_hashed_pwd}','{last_update_time}');"
        with self.extdb.begin() as connection:
            connection.execute(query)
        return last_update_time

    def log_error(self, exc_traceback):
        if self.valid_user is not None:
            logging.info(f"Logging errors to {tsh_config.username}")
            exc_traceback
            query = f"UPDATE thesillyhomedb.users \
                SET log_error = '{exc_traceback}' \
                WHERE user_id = '{tsh_config.username}';"

            with self.extdb.begin() as connection:
                connection.execute(query)


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password.encode("utf-8"), bcrypt.gensalt(15))


def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(
        plain_text_password.encode("utf-8"), hashed_password.encode("utf-8")
    )
