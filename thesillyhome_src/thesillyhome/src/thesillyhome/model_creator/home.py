import os
import json
import datetime
import pandas as pd
import pickle
import numpy as np
from sqlalchemy import create_engine

# home.py
class HomeDB:
    def __init__(self, config):
        self.config = config
        self.mydb = self.connect_db()

    def connect_db(self):
        if self.config["db_type"] == "postgres":
            connection_string = f"postgresql+psycopg2://{self.config['db_username']}:{self.config['db_password']}@{self.config['db_host']}:{self.config['db_port']}/{self.config['db_database']}"
        else:
            connection_string = f"mysql+pymysql://{self.config['db_username']}:{self.config['db_password']}@{self.config['db_host']}:{self.config['db_port']}/{self.config['db_database']}"
        return create_engine(connection_string, echo=False)

    def fetch_data(self):
        query = """
            SELECT states.state_id, states_meta.entity_id, states.state, states.last_updated_ts
            FROM states
            JOIN states_meta ON states.metadata_id = states_meta.metadata_id
            WHERE states.state != 'unavailable'
            ORDER BY states.last_updated_ts DESC
            LIMIT 100000;
        """
        return pd.read_sql(query, con=self.mydb)
