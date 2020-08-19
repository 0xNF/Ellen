import sys, os
from flask import Flask, session, request, render_template
import json
from lib import libellen
from lib import libellen_core
from datetime import datetime, timedelta, timezone

last_ran = datetime.now()
app = Flask(__name__)

def setup():
    """ initializes Ellen by grabbing configs and ensuring initial files """
    conf = libellen.read_config()
    if not conf:
        libellen.write_default_config()
        conf = libellen.read_config()
        if not conf:
            print("Failed to load config.ini, shutting down")
            sys.exit(-1)
    try:
        libellen.apply_config(conf)
    except AttributeError:
        print("Config file was corrupted. Regenerting a new default config.ini")
        libellen.write_default_config()
        conf = libellen.read_config()
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

def validate_management(obj) -> libellen_core.Config:
    """ Given a json post to the Management endpoint, validate its format """
    if obj is None:
        return None
    try:
        try:
            serverOn = obj["serverOn"] == "on"
        except:
            serverOn = True
            print(f"serverOn not found - setting to {serverOn}")

        try:
            PORT = int(obj["serverPort"])
        except:
            PORT = 5000
            print(f"serverPort not found - setting to {PORT}")

        try:
            MAX_KEEP_DAYS = int(obj["maxkeepdays"])
        except:
            MAX_KEEP_DAYS = 30
            print(f"maxkeepdays not found - setting to {MAX_KEEP_DAYS}")

        try:
            MAX_RECORD_COUNT = int(obj["maxrecordcount"])
        except:
            MAX_RECORD_COUNT = 10_000
            print(f"maxrecordcount not found - setting to {MAX_RECORD_COUNT}")

        try:
            MAX_DB_SIZE = int(obj["maxdbsize"])
        except:
            MAX_DB_SIZE = 100
            print(f"maxdbsize not found - setting to {MAX_DB_SIZE}")

        try:
            KIND = obj["kind"].upper()
        except:
            KIND = "XLS"
            print(f"kind not found - setting to {KIND}")

        try:
            # NF TODO - this, along with STORE_FULL_JSON are because bootstrap4-toggle doesnt send data if checked isnt true.
            STORE_IMAGE = obj["storeimage"].lower() == "on"
        except:
            STORE_IMAGE = False
            print(f"storeimage not found - setting to {STORE_IMAGE}")

        try:
            STORE_IMAGE_KIND = obj["storeimagekind"].upper()
        except:
            STORE_IMAGE_KIND = "FACE"
            print(f"storeimagekind not found - setting to {STORE_IMAGE_KIND}")

        try:
            STORE_FULL_JSON = obj["storefulljson"].lower() == "on"
        except:
            STORE_FULL_JSON = False
            print(f"storefulljson not found - setting to {STORE_FULL_JSON}")

        try:
            TIMEZONE = obj["timezone"].upper()
        except:
            TIMEZONE = "Local"
            print(f"timezone not found - setting to {TIMEZONE}")
        
        try:
            OUTPUT_DIR = obj["outputdirectory"]
        except:
            OUTPUT_DIR = "./"
            print(f"outputdirectory not found - setting to {OUTPUT_DIR}")

        config: libellen_core = libellen_core.Config(STORE_FULL_JSON, STORE_IMAGE,
            STORE_IMAGE_KIND, MAX_DB_SIZE, MAX_RECORD_COUNT,
            MAX_KEEP_DAYS, libellen.CONFIG.SAVE_PATH, OUTPUT_DIR, KIND, PORT,
            TIMEZONE)
        return config
    except:
        return None
    return None
    

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

@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    return 'Ellen is Running'


@app.route("/", methods=["GET"])
def mainpage():
    return render_template("index.html", title="Management", config=libellen.CONFIG)

# # # # # # # # # # # # # #
# Management Page Routes  #
# # # # # # # # # # # # # #
@app.route("/manage/updateconfig", methods=["POST"])
def post_config():
    """ Receives new config data from the Save button """
    res = {}
    conf = validate_management(request.form)
    if not conf:
        res["error"] = "received post data wasn't a valid Management Endpoint formatted JSON object"
        return res, 400
    libellen.write_custom_config(conf)
    return 'Updated config settings', 200

@app.route("/manage/newconfig", methods=["POST"])
def regenerate_config():
    try:
        os.remove("./config.ini")
        print("Deleted existing config.ini")
    except FileNotFoundError:
        print("No pre-existing config.ini found. Continuing.")
    libellen.write_default_config()
    setup()
    res = "Successfully regenerated new config.ini file"
    return res, 200

@app.route('/manage/reload', methods=["POST"])
def relod():
    """ re-reads the config.ini and reloads its settings """
    try:
        setup()
        return "Successfully reloaded config options"
    except Exception as e:
        return str(e), 500

# setup will always run, either through invocation via `Flask run` or from direct `main.
# in case of `Flask run`, server port will be ignored and will always be `5000`. For custom port,
# call Ellen directly such that the main method runs
setup()
if __name__ == "__main__":
    app.run(port=libellen.CONFIG.PORT)