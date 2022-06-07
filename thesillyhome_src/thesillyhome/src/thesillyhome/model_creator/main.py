# Library imports
# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config
from thesillyhome.model_creator.parse_data import parse_data_from_db
from thesillyhome.model_creator.learning_model import train_model
import logging
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    actuators = tsh_config.actuators
    sensors = tsh_config.sensors
    model_name_version = tsh_config.model_name_version
    tsh_config.replace_yaml()
    parse_data_from_db()
    train_model(model_name_version)
