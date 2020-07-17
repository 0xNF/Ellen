import sys
from flask import Flask, session, request
import json
from lib import libellen

app = Flask(__name__)

def setup():
    """ initializes Ellen by grabbing configs and ensuring initial files """
    if not libellen.read_config():
        libellen.write_default_config()
        if not libellen.read_config():
            sys.exit(-1)
    libellen.SetActiveStore(libellen.KIND)
    libellen.InitBackingStore()
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
        return res, 500
    except RuntimeError as e:
        res["error"] = str(e)
        return res, 500
    except Exception as e:
        res["error"] = str(e)
        return res, 500

@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    return 'Ellen is Running'