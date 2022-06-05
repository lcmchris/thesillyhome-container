echo "Starting to parse DB data"
# python3 -m thesillyhome.model_creator.main
python3 -m thesillyhome.model_creator.main


echo "Starting Appdaemon"
eval "echo \"$(</thesillyhome_src/appdaemon/appdaemon.yaml)\"" > /thesillyhome_src/appdaemon/appdaemon.yaml
nohup appdaemon -c /thesillyhome_src/appdaemon/ &

echo "Starting frontend on 0.0.0.0:2300"
PORT=2300 node /thesillyhome_src/frontend/build/index.js
