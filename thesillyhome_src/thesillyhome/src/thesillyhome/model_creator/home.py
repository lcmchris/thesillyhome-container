# Library imports
from datetime import datetime
import mysql.connector
import pandas as pd
import os.path
import logging

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

    def get_data(self, from_cache=False):
        if from_cache and os.path.exists(f"{tsh_config.data_dir}/parsed/all_states.pkl"):
            logging.info("Using cached all_states.pkl")
            return pd.read_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        mydb = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
        )
        mycursor = mydb.cursor(dictionary=True)
        query = f"SELECT entity_id, state,\
            last_changed from \
            {self.database}.states ORDER BY last_changed DESC;"

        mycursor.execute(query)
        myresult = mycursor.fetchall()
        df = pd.DataFrame.from_dict(myresult)

        df.to_csv(f"{tsh_config.data_dir}/parsed/all_states.csv")
        df.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")

        return df
