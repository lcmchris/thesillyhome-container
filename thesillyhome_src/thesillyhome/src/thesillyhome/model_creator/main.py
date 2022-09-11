# Library imports
# Local application imports
from thesillyhome.model_creator.read_config_json import replace_yaml
from thesillyhome.model_creator.read_config_json import run_cron
from thesillyhome.model_creator.parse_data import parse_data_from_db
from thesillyhome.model_creator.learning_model import train_all_actuator_models
from thesillyhome.model_creator.logger import add_logger

if __name__ == "__main__":
    add_logger()
    replace_yaml()
    parse_data_from_db()
    train_all_actuator_models()
    run_cron()
