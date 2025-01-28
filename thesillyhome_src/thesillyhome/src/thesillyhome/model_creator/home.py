# Library imports
from datetime import datetime
import pandas as pd
import logging
from sqlalchemy import create_engine
import thesillyhome.model_creator.read_config_json as tsh_config

"""
Retrieve and process data from Home Assistant database
"""


class HomeDB:
    def __init__(self):
        self.host = tsh_config.db_host
        self.port = tsh_config.db_port
        self.username = tsh_config.db_username
        self.password = tsh_config.db_password
        self.database = tsh_config.db_database
        self.db_type = tsh_config.db_type
        self.mydb = self.connect_db()

    def connect_db(self):
        if self.db_type == "postgres":
            return create_engine(
                f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
                echo=False,
            )
        elif self.db_type == "mariadb":
            return create_engine(
                f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
                echo=False,
            )
        else:
            raise Exception(f"Unsupported DB type: {self.db_type}")

    def get_data(self) -> pd.DataFrame:
        logging.info("Querying Home Assistant database for entity data.")

        # Optimierte Abfrage
        query = f"""
        WITH ranked_states AS (
            SELECT 
                states.state_id AS state_id,
                states_meta.entity_id AS entity_id,
                states.state AS state,
                states.last_updated_ts AS last_updated,
                states.old_state_id AS old_state_id,
                ROW_NUMBER() OVER (
                    PARTITION BY states_meta.entity_id
                    ORDER BY states.last_updated_ts DESC
                ) AS row_num_newest,
                ROW_NUMBER() OVER (
                    PARTITION BY states_meta.entity_id
                    ORDER BY states.last_updated_ts ASC
                ) AS row_num_oldest
            FROM states
            JOIN states_meta ON states.metadata_id = states_meta.metadata_id
            WHERE states_meta.entity_id IN ({str(tsh_config.devices)[1:-1]})
                AND states.state != 'unavailable'
                AND states.last_updated_ts IS NOT NULL
                AND states.old_state_id IS NOT NULL
        )
        SELECT 
            state_id,
            entity_id,
            state,
            last_updated,
            old_state_id
        FROM ranked_states
        WHERE row_num_newest <= 100 OR row_num_oldest <= 100
        ORDER BY entity_id, last_updated ASC;
        """

        # Abfrage der Datenbank
        with self.mydb.connect() as con:
            con = con.execution_options(stream_results=True)
            list_df = [
                df
                for df in pd.read_sql(
                    query,
                    con=con,
                    index_col="state_id",
                    parse_dates=["last_updated"],
                    chunksize=1000,
                )
            ]
            df_output = pd.concat(list_df)

        # Daten speichern und zurückgeben
        df_output.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        return df_output

    def prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info("Preparing DataFrame for analysis.")

        # Pivotieren der Tabelle
        df_pivoted = df.pivot(index="state_id", columns="entity_id", values="state")

        # Domains und Kategorien in Home Assistant
        domains_to_columns = {
            "light": "light",
            "switch": "light",
            "sensor": "sensor",
            "binary_sensor": "sensor",
            "input_boolean": "helper",
            "input_number": "helper",
            "input_text": "helper",
            "input_select": "helper",
            "input_datetime": "helper",
            "input_button": "helper",
            "cover": "cover",
            "media_player": "media_player",
            "person": "person",
            "sun": "sun",
            "temperature": "temperature",
            "humidity": "humidity",
            "illuminance": "illuminance",
            "current": "current",
            "power": "power",
            "energy": "energy",
            "volume": "volume",
            "pressure": "pressure",
            "voltage": "voltage",
            "lux": "lux",
        }

        # Dynamische Spaltenerkennung
        related_columns = []
        for domain, category in domains_to_columns.items():
            matching_columns = [col for col in df_pivoted.columns if domain in col]
            if matching_columns:
                related_columns.extend(matching_columns)

        # Fehlende Spalten ergänzen
        if not related_columns:
            logging.warning("No related columns found. Adding placeholders.")
            placeholders = ["temperature", "light"]
            for placeholder in placeholders:
                df_pivoted[placeholder] = 0
            related_columns = placeholders

        # Fehlende Werte auffüllen und numerisch konvertieren
        df_pivoted.fillna(0, inplace=True)
        df_pivoted = df_pivoted.apply(pd.to_numeric, errors="coerce").fillna(0)

        logging.info(f"Prepared DataFrame with related columns: {related_columns}")
        return df_pivoted
