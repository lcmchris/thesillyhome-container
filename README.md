# Welcome to the thesillyhome-container

# Introduction

Smart homes aren’t very smart. Managing all your device automation rules is tedious. 

That’s why The Silly Home aims to transform the static rules paradigm into a dynamic AI based approach to the connected home.

Find out more at our homepage https://thesillyhome.com/.

This repo is a docker-container built to be used with Homeassistant.
</br></br>

# How it works

Our intuition is that with enough sensor data, we can build an accurate model to predict your future device states based on your historical device states. 

### Design

Terminology:
- actuators = Any entity's state you want to create a model and predict for. ie. living_room_light_1.state, living_room_light_2.state
- sensors = Any entities that act as the triggers and conditions. ie. sensor.occupancy
- devices = actuators + sensors

#### 1. Data extraction 
Homeassistant stores state data. This step extracts and parses this data into a machine learning (‘ML’) trainable format (hot encoded categorical values, constant status publish vs state changes etc.). 

The end output frame is munged to show for each state published for an actuator, the state of other sensors and actuators.

The data is structured in a csv and formatted the following way:
actuators, states, created, duplicate, sensor1, sensor2, sensor3, sensor4...

#### 2. Learning model 
As a phase one, our focus will be to predict lights
At the moment a simple sklearn Decision Tree model is used.

There are additional features aimed to improve the accuracy:
Higher weighting for more recent data
Using the Last state as a feature input.

#### 3. Appdaemon Execution 
For ease of deployment, the decision was made to leverage Appdaemon in order to use the prediction models created in real time!

For each sensor change there is a request to predict the new states for actuators and perform them.

### Architecture diagram 
![alt text](https://github.com/lcmchris/thesillyhome-container/blob/master/doc/arch_diagram.png)

</br></br>
# Installation guide

### Dependencies

Homeassistant OS or Container.

Recorder component enabled using mariadb or postgreSQL with auto_purge disabled.

## Setup 
There is support for both types of Homeassistant installations:

### Setup for Homeassistant OS
Install the Homeassistant add-on using [thesillyhome-addon-repo](https://github.com/lcmchris/thesillyhome-addon-repo).


### Setup for Homeassistant Container
To install this container, run the following:
```
git clone git@github.com:lcmchris/thesillyhome-container.git

docker volume create thesillyhome_config
# Find the path to volume docker volume inspect thesillyhome_config or \\wsl$\docker-desktop-data\data\docker\volumes
cp thesillyhome_src\data\config\options.json <path_to_volume>
# Amend the copied options.json

docker-compose up -d
```

### Configuration file

```
actuactors_id: List of all entity_ids of actuators.
sensors_id: List of all entity_ids of sensors.
db_options: All settings for connecting to the homeassistant database
  db_password: Database password 
  db_username: Database username e.g homeassistant
  db_host:  Database host 192.168.1.100
  db_port:  Database port '3306'
  db_database:  Database name homeassistant, or the sqlite db filename (`home-assistant_v2.db` is the default)
  db_type:  Database type. Only {sqlite,mariadb,postgres} is supported
 ha_options: All settings for connecting to homeassistant. These settings are only required for Homeassistant Container setup.
  ha_url: IP of your homeassistant
  ha_token: Long lived access token. This is required for the Appdaemon.
 ```
 
See the [example config file](https://github.com/lcmchris/thesillyhome-container/blob/master/thesillyhome_src/data/config/options.json) for more details
  
</br></br>
# Contribution guide

### Support
Reach out in our [Discord](https://discord.gg/haVav7uXm8) for support on issues.
Raise code issues in GitHub and tag as bugs.

### Feature Requests
Discuss features in our [Discord](https://discord.gg/haVav7uXm8).
Raise issues on GitHub and tag as enhancements.

</br></br>
# Feature Roadmap

Please see [The Silly Home Features Roadmap Git Projects](https://github.com/users/lcmchris/projects/1) 

### Routine extraction?
There is an open thought that having these untrained, underperforming models (at this stage) to directly manage your home is a bad idea. A perhaps better one is to make it predict your required routines.

### Model Performance dashboard?
Having a black box is probably not ideal for The Silly Home, adding some visibility on the models giving performance will help let you pick and choose the models to activate.
