$env:FLASK_APP="./src/server/server.py"
$env:FLASK_ENV="development"
$env:FLASK_DEBUG=0
python3.8 -m flask run