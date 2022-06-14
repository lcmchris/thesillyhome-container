import json
import os

if os.environ.get("HA_ADDON") == "true":
    data_dir = "/data"
    f = open(f"{data_dir}/options.json")
else:
    data_dir = "/thesillyhome_src/data"
    f = open(f"{data_dir}/config/options.json")

options = json.load(f)

actuators = options["actuactors_id"]
sensors = options["sensors_id"]
db_options = options["db_options"][0]
db_password = db_options["db_password"]
db_database = db_options["db_database"]
db_username = db_options["db_username"]
db_type = db_options["db_type"]

db_host = db_options["db_host"]
db_port = db_options["db_port"]

model_name = "Base"
model_version = "0.0.0"
model_name_version = f"{model_name}_{model_version}"


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

    if os.environ.get("HA_ADDON") == "true":
        with open("/thesillyhome_src/appdaemon/appdaemon.yaml", "r") as f:
            content = f.read()
            content = content.replace("<ha_url>", "http://supervisor/core")
            content = content.replace("<ha_token>", "$SUPERVISOR_TOKEN")

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
