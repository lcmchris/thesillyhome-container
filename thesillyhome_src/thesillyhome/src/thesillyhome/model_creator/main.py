# Library imports
# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config
from thesillyhome.model_creator.parse_data import parse_data_from_db
from thesillyhome.model_creator.learning_model import train_all_actuator_models
import logging
import sys

if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        filename="/thesillyhome_src/log/thesillyhome.log",
        encoding="utf-8",
        level=logging.INFO,
        format=FORMAT,
    )
    root = logging.getLogger()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    actuators = tsh_config.actuators
    sensors = tsh_config.sensors
    tsh_config.replace_yaml()
    parse_data_from_db()
    train_all_actuator_models()
    tsh_config.run_cron()
