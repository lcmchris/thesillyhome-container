# Welcome to the thesillyhome-container

# Introduction



# Installation guide


## HA Addon Setup
In this setup, we have a pip installable repo that hosts all the code https://github.com/lcmchris/thesillyhome-addon-repo. This is installed onto the addon container and is built onto the addon-image.
This addon uses the Appdaemon to control devices. This decision was made due to the simplicity of its implementation


# Contribution guide


# Architecture diagram 


- This repository is an addo-on that tries to help apply ML to your homeassistance.
- This aims to act as a proof of concept that applying ML to homeautomation works and a future with J.A.R.V.I.S is closer than we thought.
- This is opensource but a wider vision is to apply this to all homeautomation platforms (think APIs and centralised AI models). This is the tenet of <a href="https://thesillyhome.com/about-us/#our-mission">The silly home</a>.



# How this works
<h2> ML design </h2>

Terminology used :
actuators = Any entity's state you want to create a model and predict for. ie. living_room_light_1.state, living_room_light_2.state
sensors = Any entities that act as the triggers and conditions. ie. sensor.occupancy
devices = actuators + sensors

Intuition:
With a new device state change, predict if any other actuators need to change.
1 Model per actuator

1) Data extraction
2) Learning model
3) Appdaemon Execution


<h2> Data extraction </h2>
Homeassistant stores state data. This step extracts and parses this data into a ML trainable format (hot encoded of categorical values, constant status publish vs state changes etc..). 

The end output frame is munged to show for each state published for an actuator, the state of other sensors and actuators.

The data is strucutred in a csv and looks like this:
actuators, states, created, duplicate, senor1, sensor2, sensor3, sensor4...

<h2> Learning model </h2>
As a phase one, our focus will be to predict lights using motion sensors, light sensors, other lights, device location, weather as inputs.
Only sklearn Decision Tree model is used.

<h2> Appdaemon Execution </h2>
For ease of deployment, the decision was made to leverage Appdaemon in order to use the prediction models created in real time!
For each sensor change there is a request to predict the new states for actuators and performs them.


Add-on documentation: N/A



# Features Roadmap

<h3> Routine extraction? </h3>
There is an open thought that having these untrained, underperforming models (at this stage) to directly manage your home is a bad idea. A perhapes better one is to make it predict your required routines.

<h2> Model Performance dashboard? </h2>
Having a black box is probably not ideal for The silly home, adding some visibility on the models giving performance will help let you pick and choose the models to activate.
