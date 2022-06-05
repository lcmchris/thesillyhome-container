# thesillyhome

This is a repo for routine creation for HomeAssistant.

Setup:
In this setup, we have this repo that hosts all the code that is installed by the https://github.com/lcmchris/thesillyhome-addon-repo and is installed onto the container.

The stages of processing is as follows:

1) Data extraction
2) Learning model
3) Appdaemon Execution
X) Routine extraction?
X) Model Performance dashboard?

<h2> Data extraction </h2>
HomeAssistant stores state data. Extract and parse this data into a ML readable format (hot encoded time/date etc..).
The data is strucutred in a csv and looks like this:
actuators, states, created, duplicate, senor1, sensor2, sensor3, sensor4...


<h2> Learning model </h2>
As a phase one, our focus will be to predict lights using motion sensors, light sensors, other lights, device location, weather as inputs.
Feel free to suggest any 

<h2> Appdaemon Execution </h2>
For ease of deployment, the decision was made to leverage Appdaemon in order to use the prediction models created in real time!
For each sensor change there is a request to predict the new states for actuators and performs them.

<h2> Routine extraction? </h2>
There is an open thought that having these untrained, underperforming models (at this stage) to directly manage your home is a bad idea. A perhapes better one is to make it predict your required routines.

<h2> Model Performance dashboard? </h2>
Having a black box is probably not ideal for The silly home, adding some visibility on the models giving performance will help let you pick and choose the models to activate.
