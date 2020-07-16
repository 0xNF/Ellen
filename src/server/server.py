from flask import Flask
app = Flask(__name__)

@app.route('/savegorilla', methods=["POST"])
def save_gorilla():
    """ receives gorilla formatted data, and if valid, saves to the backing store """
    # NF TODO
    return 'Hello, World!'

@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    return 'Ellen is Running'