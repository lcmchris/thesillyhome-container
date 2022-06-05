# Library imports
# Local application imports
import thesillyhome.model_creator.read_config_json as tsh_config
from thesillyhome.model_creator.parse_data import parse_data_from_db
from thesillyhome.model_creator.learning_model import train_model

if __name__ == "__main__":

    actuators = tsh_config.actuators
    sensors = tsh_config.sensors
    model_name_version = tsh_config.model_name_version
    tsh_config.replace_yaml()
    parse_data_from_db(actuators, sensors)
    train_model(actuators, model_name_version)
