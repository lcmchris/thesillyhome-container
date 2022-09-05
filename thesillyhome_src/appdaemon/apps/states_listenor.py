# Library imports

import appdaemon.plugins.hass.hassapi as hass
import pandas as pd
from sqlalchemy import create_engine
import time
import threading
import json
from datetime import datetime
import uuid

# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config


class StatesListenor(hass.Hass):
    def initialize(self):
        self.extdb = self.connect_external_db()
        self.handle = self.listen_state(self.state_handler)
        self.user = hex(uuid.getnode())

        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome state listenor fully initialized!")

    def state_handler(self, entity, attribute, old, new, kwargs):
        data_export_event = {
            "snapshot_time": str(datetime.now()),
            "get_state_json": json.dumps(self.get_state()),
            "type": "chng",
            "user_id": self.user,
        }
        data_event = pd.DataFrame(data_export_event, index=[0])
        data_event.to_sql(
            "states_snapshots", con=self.extdb, index=False, if_exists="append"
        )

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
