# Library imports
import subprocess
import json
import os
import logging
from cryptography.fernet import Fernet


data_dir = "/thesillyhome_src/data"

if os.environ.get("HA_ADDON") == "true":
    config_file = open(f"/data/options.json")
else:
    config_file = open(f"/thesillyhome_src/data/config/options.json")

options = json.load(config_file)

# Mandatory
username = options.get("username")
password = options.get("password")
actuators = options.get("actuactors_id")
sensors = options.get("sensors_id")
devices = actuators + sensors
db_options = options.get("db_options")[0]
db_password = db_options.get("db_password")
db_database = db_options.get("db_database")
db_username = db_options.get("db_username")
db_type = db_options.get("db_type")
db_host = db_options.get("db_host")
db_port = db_options.get("db_port")

# Defaults
share_data = options.get("share_data", True)
autotrain = options.get("autotrain", True)
autotrain_cadence = options.get("autotrain_cadence", "0 0 * * 0")

# Non-user config

f = Fernet(b"w2PWqacy0_e4XZ2Zb8BU6GauyRgiZXw12wbmi0A6CjQ=")
extdb_password = f.decrypt(
    b"gAAAAABi_2EebCwQSA3Lbk3MPCXvH3I6G-w8Ijt0oYiqfmUdzdrMjVRQuTqbpqK-DQCsyVliUWFsvd1NulF-WBsLKOpwmiCp-w=="
).decode("utf-8")
extdb_database = "thesillyhomedb"
extdb_username = "thesillyhome_general"
extdb_host = "thesillyhomedb.cluster-cdioawtidgpj.eu-west-2.rds.amazonaws.com"
extdb_port = 3306


# Other helpers
def extract_float_sensors(sensors: list):
    float_sensors_types = ["lux"]
    float_sensors = []
    for sensor in sensors:
        if sensor.split("_")[-1] in float_sensors_types:
            float_sensors.append(sensor)
    return float_sensors


float_sensors = extract_float_sensors(sensors)

output_list_og = ["entity_id", "state"]
output_list = ["entity_id", "state", "last_updated"]
output_list_dup = ["entity_id", "state", "last_updated", "duplicate"]


def replace_yaml():
    if os.environ.get("HA_ADDON") == "true" and options.get("ha_options") == None:
        with open("/thesillyhome_src/appdaemon/appdaemon.yaml", "r") as f:
            content = f.read()
            supervisor_token = os.environ["SUPERVISOR_TOKEN"]
            content = content.replace("<ha_url>", "http://supervisor/core")
            content = content.replace("<ha_token>", f"""{supervisor_token}""")

        with open("/thesillyhome_src/appdaemon/appdaemon.yaml", "w") as file:
            file.write(content)
        return
    else:
        ha_options = options["ha_options"][0]
        ha_url = ha_options["ha_url"]
        ha_token = ha_options["ha_token"]

        with open("/thesillyhome_src/appdaemon/appdaemon.yaml", "r") as f:
            content = f.read()
            content = content.replace("<ha_url>", ha_url)
            content = content.replace("<ha_token>", ha_token)

        with open("/thesillyhome_src/appdaemon/appdaemon.yaml", "w") as file:
            file.write(content)
        return


def run_cron():
    if autotrain == True:
        with open("/thesillyhome_src/startup/crontab", "r") as f:
            content = f.read()
            content = content.replace("<autotrain_cadence>", autotrain_cadence)
        with open("/thesillyhome_src/startup/crontab", "w") as file:
            file.write(content)

        subprocess.run(["crontab", "/thesillyhome_src/startup/crontab"])
        logging.info(f"Runnining cron with cadence {autotrain_cadence}")
        return
    else:
        return
