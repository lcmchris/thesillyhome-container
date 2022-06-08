# Library imports
from datetime import datetime
import mysql.connector
import psycopg2
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
        self.db_type = tsh_config.db_type

    def get_data(self, from_cache=False):
        if from_cache and os.path.exists(
            f"{tsh_config.data_dir}/parsed/all_states.pkl"
        ):
            logging.info("Using cached all_states.pkl")
            return pd.read_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")

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
            logging.info('DB type is mariadb or postgres.')
            
        query = f"SELECT entity_id, state,\
            last_updated from \
            states ORDER BY last_updated DESC;"
        mycursor = mydb.cursor()

        mycursor.execute(query)
        myresult = mycursor.fetchall()

        # Extract the column names
        col_names = []
        for elt in mycursor.description:
            col_names.append(elt[0])
        df = pd.DataFrame.from_dict(myresult)
        df.columns = col_names
        df.to_csv(f"{tsh_config.data_dir}/parsed/all_states.csv")
        df.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")

        return df


class Postgresql(homedb):
    """postgresql subclass using %s.
    unique postgresql elements go here"""

    def __init__(self):
        # initialise the superclass
        homedb.__init__(self)

        self.wildcard = "%s"
        self.uncommon_value = "py hole"
        # other unique values go here


class Mariadb(homedb):
    def __init__(self):
        # initialise the superclass
        homedb.__init__(self)

        self.wildcard = "?"
        # other unique values go here

    # other methods
