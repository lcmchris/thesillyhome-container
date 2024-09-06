# Library imports
from datetime import datetime
import pandas as pd
import logging
from sqlalchemy import create_engine
import json

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config

class homedb:
    def __init__(self):
        self.host = tsh_config.db_host
        self.port = tsh_config.db_port
        self.username = tsh_config.db_username
        self.password = tsh_config.db_password
        self.database = tsh_config.db_database
        self.db_type = tsh_config.db_type
        self.from_cache = False
        self.mydb = self.connect_internal_db()

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

    def get_data(self) -> pd.DataFrame:
        logging.info("Getting data from internal homeassistant db")

        if self.from_cache:
            logging.info("Using cached all_states.pkl")
            return pd.read_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        
        logging.info("Executing query")

        query = """
            SELECT
                states.state_id AS state_id,
                states.entity_id AS entity_id,
                states.state AS state,
                states.last_updated AS last_updated_ts,
                states.old_state_id AS old_state_id,
                state_attributes.shared_data AS shared_data
            FROM states
            JOIN state_attributes ON states.attributes_id = state_attributes.attributes_id
            WHERE states.entity_id IN ({devices})
                AND states.state != 'unavailable'
                AND states.entity_id IN (
                    SELECT entity_id
                    FROM states
                    WHERE state != 'unavailable'
                    GROUP BY entity_id
                    HAVING COUNT(*) > 50
                )
            ORDER BY states.entity_id, states.last_updated DESC
            LIMIT 1000;  -- Adjust this limit as needed
        """.format(devices=str(tsh_config.devices)[1:-1])

        with self.mydb.connect() as con:
            con = con.execution_options(stream_results=True)
            list_df = [
                df
                for df in pd.read_sql(
                    query,
                    con=con,
                    index_col="state_id",
                    parse_dates=["last_updated_ts"],
                    chunksize=50,
                )
            ]
            df_output = pd.concat(list_df)
        
        df_output.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        return df_output
