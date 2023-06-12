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
                raise Exception(f"Invalid DB type: {self.db_type}.")
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
            states_meta.entity_id AS entity_id,
            states.state AS state,
            states.last_changed AS last_changed,
            states.last_updated AS last_updated,
            states.old_state_id AS old_state_id
        FROM
            states
            JOIN states_meta ON states.metadata_id = states_meta.metadata_id
        WHERE
            states_meta.entity_id IN (
                'switch.solarakkuladung',
                'switch.lichtschalter_buero_s1',
                'switch.shelly_shsw_1_e8db84a1f048',
                'switch.lichtschalter_abstellraum_s1',
                'switch.lichtschalter_og_flur_s1',
                'switch.lichtschalter_gaestezimmer_s1',
                'switch.lichtschalter_hwr_s1',
                'switch.lichtschalter_dg_flur_s1',
                'switch.lichtschalter_schlafzimmer_s1',
                'switch.lichtschalter_ankleidezimmer_s1',
                'switch.lichtschalter_lichtschalter_treppe_ug_s1',
                'light.led_schlafzimmer',
                'switch.lichtschalter_badezimmer_s1',
                'input_boolean.helper_presence_buro',
                'input_boolean.helper_presence_gastezimmer',
                'input_boolean.helper_presence_schlafzimmer',
                'input_boolean.helper_presence_ankleidezimmer',
                'switch.lichtschalter_treppe_ug_unten_s1',
                'switch.lichtschalter_eingang',
                'switch.lichtschalter_kueche_s1',
                'switch.lichtschalter_essbereich_s1',
                'light.led_tv_wohnzimmer',
                'input_boolean.gaste_wc_occupied',
                'switch.lichtschalter_gaestewc_1',
                'switch.nuki_nuki_auto_lock',
                'light.led_garten',
                'switch.shelly_shsw_25_10521cf0c8fc_1',
                'switch.lichtschalter_wohnzimmer_s2',
                'switch.shelly_shsw_25_10521cf0c8fc_2',
                'vacuum.berta',
                'media_player.fernseher_wohnzimmer',
                'light.duschen',
                'input_boolean.at_home',
                'input_boolean.alarmanlage_away',
                'input_boolean.simon_schlafen',
                'input_boolean.kristina_schlafen',
                'switch.steckdose_berta'
            )        
        ORDER BY
            last_updated DESC
        LIMIT
            100000;
        """

        with self.mydb.connect() as con:
            con = con.execution_options(stream_results=True)
            df_output = pd.read_sql(
                query,
                con=con,
                index_col="state_id",
                parse_dates=["last_updated"]
            )
        df_output.to_pickle(f"{tsh_config.data_dir}/parsed/all_states.pkl")
        return df_output


def parse_data_from_db():
    db = homedb()
    data = db.get_data()
    # Perform further processing with the data


parse_data_from_db()

