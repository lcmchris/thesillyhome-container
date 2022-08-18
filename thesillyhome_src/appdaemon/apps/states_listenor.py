# Library imports

import appdaemon.plugins.hass.hassapi as hass
import pandas as pd
from sqlalchemy import create_engine
import time
import threading
import json
from datetime import datetime


class StatesListenor(hass.Hass):
    def initialize(self):
        self.extdb = self.connect_external_db()
        self.handle = self.listen_state(self.state_handler)
        self.loop = self.periodic_log_state_daemon()

        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome state listenor fully initialized!")

    def periodic_log_state_daemon(self):
        thread = threading.Thread(target=self.periodic_log_state, daemon=True)
        thread.start()

    def periodic_log_state(self):
        while True:
            data_export = {
                "snapshot_time": str(datetime.now()),
                "get_state_json": json.dumps(self.get_state()),
                "type": "peri",
            }
            data = pd.DataFrame(data_export, index=[0])
            data.to_sql(
                "states_snapshots", con=self.extdb, index=False, if_exists="append"
            )
            time.sleep(5.0 - time.time() % 5.0)

    def state_handler(self, entity, attribute, old, new, kwargs):
        devices = [
            "light.corridor_lights",
            "light.bathroom_lights",
            "light.bedroom_ceiling_light",
            "light.bedroom_sidetable_lamp",
            "switch.livingroom_entrance_switch_right",
            "switch.livingroom_entrance_switch_center",
            "switch.livingroom_entrance_switch_left",
            "binary_sensor.corridor_end_sensor_occupancy",
            "binary_sensor.corridor_entrance_sensor_occupancy",
            "binary_sensor.livingroom_desk_sensor_occupancy",
            "binary_sensor.bedroom_entrance_sensor_occupancy",
            "binary_sensor.bathroom_entrance_sensor_occupancy",
            "binary_sensor.chris_phone_is_charging",
            "binary_sensor.livingroom_deskchair_sensor_vibration",
            "binary_sensor.livingroom_sofa_sensor_occupancy",
            "sun.sun",
            "weather.home",
        ]
        if entity in devices:
            data_export_event = {
                "snapshot_time": str(datetime.now()),
                "get_state_json": json.dumps(self.get_state()),
                "type": "chng",
            }
            data_event = pd.DataFrame(data_export_event, index=[0])
            data_event.to_sql(
                "states_snapshots", con=self.extdb, index=False, if_exists="append"
            )

    def connect_external_db(self):
        host = "thesillyhomedb-instance-1.cdioawtidgpj.eu-west-2.rds.amazonaws.com"
        port = 3306
        user = "admin"
        password = "vNwtmCh2NX5fm8B"
        database = "thesillyhomedb"
        extdb = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", echo=False
        )
        return extdb
