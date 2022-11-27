import thesillyhome.model_creator.read_config_json as tsh_config
import logging


def base_config_checks():
    check_mandatory_fields(
        [
            ("actuators", tsh_config.actuators),
            ("sensors", tsh_config.sensors),
            ("db_options", tsh_config.db_options),
            ("db_password", tsh_config.db_password),
            ("db_database", tsh_config.db_database),
            ("db_username", tsh_config.db_username),
            ("db_type", tsh_config.db_type),
            ("db_host", tsh_config.db_host),
            ("db_port", tsh_config.db_port),
        ]
    )
    check_db(tsh_config.db_type)


def check_db(db_type):
    if db_type not in ["mariadb", "postgres"]:
        raise Exception("Make sure your dbtype is either `mariadb` or `postgres`.")


def check_mandatory_fields(mandatory_fields: list):
    for name, field in mandatory_fields:
        if field is None:
            raise KeyError(
                f"Missing Mandatory field {name}, please add this to the config file."
            )


def check_actuators_ids(actuators_id):
    if len(actuators_id > 10):
        logging.warning(
            "In the current implementation, the suggestion is to use <= 10 actuators as it may causes throttling issues with Appdaemon."
        )


def check_device_ids(in_data_ids):
    invalid_actuators_ids = set(tsh_config.actuators) - set(in_data_ids)
    invalid_sensors_ids = set(tsh_config.sensors) - set(in_data_ids)
    if invalid_actuators_ids:
        for invalid in list(invalid_actuators_ids):
            tsh_config.actuators.remove(invalid)
        logging.warning(
            f"Cannot find actuator cases for ids {invalid_actuators_ids}. Removing..."
        )
    if invalid_sensors_ids:
        for invalid in list(invalid_sensors_ids):
            tsh_config.sensors.remove(invalid)
        logging.warning(
            f"Cannot find sensor cases for ids {invalid_sensors_ids}. Removing..."
        )
    if len(invalid_actuators_ids) == len(tsh_config.actuators):
        raise Exception(f"No valid actuator cases for all ids {invalid_actuators_ids}")
    if len(invalid_sensors_ids) == len(tsh_config.actuators):
        raise Exception(f"No valid sensor cases for all ids {invalid_actuators_ids}")
