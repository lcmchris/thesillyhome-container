# Library imports
from cmath import exp
from datetime import datetime
from select import select
import string
from time import ctime
import mysql.connector
import psycopg2
import pandas as pd
import os.path
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
        self.mydb = self.connect_internal_db()
        self.extdb = self.connect_external_db()

    def connect_internal_db(self):
        if self.db_type == "mariadb":
            mydb = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
            )

        elif self.db_type == "postgres":
            mydb = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
            )
        else:
            logging.info("DB type is mariadb or postgres.")
        return mydb

    def get_data(self, from_cache=False):
        logging.info("Getting data from internal homeassistant db")

        if from_cache and os.path.exists(
            f"{tsh_config.data_dir}/parsed/all_states.pkl"
        ):
            logging.info("Using cached all_states.pkl")
            return pd.read_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")

        query = f"SELECT \
                    state_id,\
                    entity_id  ,\
                    state  ,\
                    if(last_changed is NULL,last_updated,last_changed) as last_changed  ,\
                    last_updated  ,\
                    old_state_id \
                from states ORDER BY last_updated DESC;"
        mycursor = self.mydb.cursor()
        mycursor.execute(query)
        myresult = mycursor.fetchall()

        # Clean to DF
        col_names = []
        for elt in mycursor.description:
            col_names.append(elt[0])
        df = pd.DataFrame.from_dict(myresult)
        df.columns = col_names

        df = df.set_index("state_id")

        df.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        if self.share_data:
            logging.info("Uploading data to external db. Thanks for sharing!")

            self.upload_data(df)
        self.mydb.close()
        return df

    def connect_external_db(self):
        host = "thesillyhomedb.cluster-cdioawtidgpj.eu-west-2.rds.amazonaws.com"
        port = 3306
        user = "thesillyhome_general"
        password = "has123:ASldfa.$"
        database = "thesillyhomedb"
        extdb = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", echo=False
        )
        return extdb

    def upload_data(self, df: pd.DataFrame):

        user_id, last_update_time = self.get_user_info()
        df["user_id"] = user_id

        df = df[df["last_updated"] > last_update_time]
        if not df.empty:
            df.to_sql(name="states", con=self.extdb, if_exists="append")
            logging.info(f"Data updloaded.")

            c_time = df["last_updated"].max()
            self.update_last_update_time(user_id, c_time)

    def get_user_info(self):
        # here we use the mac address as a dummy, this is used for now until an actual login system

        user_id = hex(uuid.getnode())
        logging.info(f"Using MAC address as user_id {user_id}")

        query = f"SELECT \
                    last_update_time \
                from users where user_id = '{user_id}';"

        with self.extdb.connect() as connection:
            myresult = connection.execute(query).fetchall()

        assert len(myresult) in (0, 1)

        if len(myresult) == 1:
            last_update_time = myresult[0][0]
        else:
            last_update_time = datetime(1900, 1, 1, 0, 0, 0, 0)

        return user_id, last_update_time

    def update_last_update_time(self, user_id: string, c_time: datetime):
        logging.info(f"Updating user table with last_update_time {c_time}")
        query = f"UPDATE thesillyhomedb.users \
                SET last_update_time = '{c_time}' \
                WHERE user_id = '{user_id}';"
        with self.extdb.connect() as connection:
            connection.execute(query)
