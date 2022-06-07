import appdaemon.plugins.hass.hassapi as hass
import thesillyhome.model_creator.read_config_json as tsh_config
import pickle
import pandas as pd
from pandas import DataFrame
from sklearn.tree import DecisionTreeClassifier
from datetime import datetime
import copy
import os.path
import logging


class ModelExecutor(hass.Hass):
    def initialize(self):
        self.model_name_version = tsh_config.model_name_version
        self.handle = self.listen_state(self.state_handler)
        self.act_model_set = self.load_models()
        self.log("Hello from TheSillyHome")
        self.log("TheSillyHome has now started!")

    def load_models(self):
        '''
        Loads all models to a dictionary
        '''
        actuators = tsh_config.actuators
        act_model_set = {}
        for act in actuators:
            if os.path.isfile(f"/thesillyhome_src/data/model/{self.model_name_version}/{act}.pickle"):
                with open(
                    f"/thesillyhome_src/data/model/{self.model_name_version}/{act}.pickle", "rb"
                ) as pickle_file:
                    content = pickle.load(pickle_file)
                    act_model_set[act] = content
            else:
                logging.info(f"No model for {act}")
        return act_model_set

    def state_handler(self, entity, attribute, old, new, kwargs):
        sensors = tsh_config.sensors
        float_sensors = tsh_config.float_sensors
        self.log(f'Received state {entity}')

        if entity in sensors:
            self.log(f"<----- {entity} is {new} ----->")

            # Get feature list from parsed data header, set all columns to 0
            feature_list = pd.read_pickle(
                "/thesillyhome_src/data/parsed/act_states.pkl").columns
            feature_list = sorted(
                list(set(feature_list) -
                     set(['entity_id', 'state', "duplicate"]))
            )
            
            current_state_base = pd.DataFrame(columns=feature_list)
            current_state_base.loc[len(current_state_base)] = 0
            print (current_state_base)

            # Get current state of all sensors for model input
            df_sen_states = copy.deepcopy(current_state_base)
            for sensor in sensors:
                true_state = self.get_state(entity_id=sensor)
                if sensor not in float_sensors:
                    if f"{sensor}_{true_state}" in df_sen_states.columns:
                        df_sen_states[sensor + "_" + true_state] = 1
                elif sensor in float_sensors:
                    if (true_state) in df_sen_states.columns:
                        df_sen_states[sensor] = true_state

            # Execute all models for sensor and set states
            for act, model in self.act_model_set.items():
                # the actuators feature state should not affect the model and also the duplicate column
                cur_act_list = []
                for feature in feature_list:
                    if feature.startswith(act):
                        cur_act_list.append(feature)
                new_feature_list = sorted(list(set(feature_list) - set(cur_act_list)))
                df_sen_states_less = df_sen_states[new_feature_list]

                prediction = model.predict(df_sen_states_less)
                if prediction == 1:
                    self.log(f"Turn on {act}")
                    self.turn_on(act)
                elif prediction == 0:
                    self.log(f"Turn off {act}")
                    self.turn_off(act)
