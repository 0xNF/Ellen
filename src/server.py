import sys
from flask import Flask, session, request
import json
from lib import libellen
from datetime import datetime, timedelta

last_ran = datetime.now()

app = Flask(__name__)

def setup():
    """ initializes Ellen by grabbing configs and ensuring initial files """
    conf = libellen.read_config()
    if not conf:
        libellen.write_default_config()
        conf = libellen.read_config()
        if conf:
            print("Failed to load config.ini, shutting down")
            sys.exit(-1)
    libellen.SetActiveStore(libellen.KIND)
    libellen.InitBackingStore()
    print("Using the following config settings:")
    print(conf.__dict__)
    return

def validate_format(obj) -> bool:
    """ given a json post, check that its a valid gorilla formatted item """
    if obj is None:
        return False
    if not isinstance(obj, dict):
        return False
    if not obj.get("id"):
        return False
    common = obj.get("common")
    if not common or not isinstance(common, dict):
        return False
    if not common.get("time") or not common.get("type"):
        return False
    imgs = common.get("images")
    if imgs and not isinstance(imgs, list):
        return False
    return True

setup()

@app.route('/savegorilla', methods=["POST"])
def save_gorilla():
    """ receives gorilla formatted data, and if valid, saves to the backing store """
    global last_ran
    if (datetime.now() - timedelta(hours=1)) >= last_ran:
        print("checking for old records in storage file")
        libellen.prune()
        last_ran = datetime.now()
    j = request.json
    res = {}
    if not validate_format(j):
        res["error"] = "received post data wasn't a valid Gorilla formatted JSON object"
        return res, 400
    try:
        libellen.receive_json(j)
        id = j["id"]
        res = {
            "id": id
        }
        return res, 200
    except FileNotFoundError as e:
        res["error"] = str(e)
        return res, 501
    except RuntimeError as e:
        res["error"] = str(e)
        return res, 502
    except Exception as e:
        res["error"] = str(e)
        return res, 503


@app.route('/reload', methods=["GET"])
def relod():
    """ re-reads the config.ini and reloads its settings """
    try:
        setup()
        return {"message": "reloaded config options"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    return 'Ellen is Running'