echo "Starting frontend"
node /frontend/build/index.js

# echo "Starting to parse DB data"
# python3 -m thesillyhome.model_creator.main

# echo "Starting Appdaemon"
# eval "echo \"$(</appdaemon/appdaemon.yaml)\"" > /appdaemon/appdaemon.yaml
# appdaemon -c /appdaemon/