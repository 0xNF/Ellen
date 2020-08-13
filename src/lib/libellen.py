from typing import List, Set, Dict, Tuple, Optional
import sys, os
import sqlite3
import json
import configparser
from datetime import datetime, time, timedelta, timezone
from .libellen_xls import prune_old_data as prune_xls, ensure as ensure_xls, update_bap as update_bap_xls, update_ivar as update_ivar_xls, set_config as set_config_xls
from .libellen_sql import prune_old_data as prune_sql, ensure as ensure_sql, update_bap as update_bap_sql, update_ivar as update_ivar_sql, set_config as set_config_sql
from .libellen_core import Config, Candidate, GImage

STORE_XLS = "XLS"
STORE_SQL = "SQL"

TZ_LOCAL = "local"
TZ_UTC = "utc"

CONFIG: Config = None

_CHOSEN_STORE = None # assigned with the values from either STORE_XLS or STORE_SQL
ACTIVE_STORE = None

prune = None
ensure = None
update_bap = None
update_ivar = None
set_config = None

def apply_config(conf: Config):
    """ applies the supplied conf object to the server instance """
    global CONFIG
    CONFIG = conf
    SetActiveStore()
    InitBackingStore()
    return

def read_config() -> Config:
    """ reads the config file at the regular path, returns None if no config is found """
    global CONFIG
    conf = configparser.ConfigParser()
    if not conf.read("./config.ini"):
        return None
    try:
        MAX_KEEP_DAYS = int(conf["MAINTENANCE"]["MaxKeepDays"])
        MAX_RECORD_COUNT = int(conf["MAINTENANCE"]["MaxRecordCount"])
        MAX_DB_SIZE = int(conf["MAINTENANCE"]["MaxDbSize"])

        STORE_IMAGE = json.loads(conf["SAVE"]["StoreImage"].lower())
        STORE_IMAGE_KIND = str(conf["SAVE"]["StoreImageKind"])
        STORE_FULL_JSON = json.loads(conf["SAVE"]["StoreFullJson"].lower()) # ghetto way of converting to booleans
        DATA_DIR = str(conf["SAVE"]["DataDirectory"])
        OUTPUT_DIR = str(conf["SAVE"]["OutputDirectory"])
        KIND = str(conf["SAVE"]["Kind"])
        TIMEZONE = str(conf["SAVE"]["Timezone"])

        PORT = int(conf["SERVER"]["Port"])

        CONFIG = Config(STORE_FULL_JSON, STORE_IMAGE,
        STORE_IMAGE_KIND, MAX_DB_SIZE, MAX_RECORD_COUNT,
        MAX_KEEP_DAYS, DATA_DIR, OUTPUT_DIR, KIND, PORT,
        TIMEZONE)
        return CONFIG
    except:
        return None

def write_default_config() -> Config:
    """ creates a default Config.ini at the regular path and returns the config object """
    conf = configparser.ConfigParser()
    conf["MAINTENANCE"] = {
        "MaxKeepDays": '30',
        "MaxRecordCount": "10000",
        "MaxDbSize": "100",
    }
    conf["SAVE"] = {
        "StoreImageKind": "FACE",
        "StoreImage": "True",
        "StoreFullJson": "False",
        "DataDirectory": "./data",
        "OutputDirectory": "./",
        "Kind": "XLS",
        "Timezone": "Local"
    }
    conf["SERVER"] = {
        "Port": "5000",
    }
    with open("./config.ini", 'w') as f:
        conf.write(f)
    return conf


def InitBackingStore():
    """ Initializes the backing store and ensures it is in a writable state """
    if ensure is not None:
        ensure() # dynamic dispatch to the true storage's ensure method
        prune()
    else:
        raise Exception("No Active Store was set. Call SetActiveStore before continuing")
    return

def SetActiveStore():
    """ Sets the backing store to use. Accepted values are either XLS or SQL """
    global prune, ensure, update_bap, update_ivar
    if CONFIG.KIND == STORE_XLS:
        prune = prune_xls
        ensure = ensure_xls
        update_bap = update_bap_xls
        update_ivar = update_ivar_xls
        set_config = set_config_xls
    elif CONFIG.KIND == STORE_SQL:
        prune = prune_sql
        ensure = ensure_sql
        update_bap = update_bap_sql
        update_ivar = update_ivar_sql
        set_config = set_config_sql
    else:
        raise Exception("Backing store must be oneof 'XLS', 'SQL'")
    set_config(CONFIG)
    return

def receive_json(jobj: dict) -> int:
    """ given an ivar event, updates the data storage with the received data, according to the storage preferences.
    returns 0 for success, or throws an error otherwise
    """
    try:
        ensure() # it is possible that the output file was moved or deleted during server execution. Put it back 
    except Exception as e:
        raise FileNotFoundError("Failed to re-create storage file", e)
    try:
        id = jobj["id"]
        timestamp = datetime.strptime(jobj["common"]["time"], "%Y-%m-%dT%H:%M:%S.%fZ")
        if CONFIG.TIMEZONE.lower() == TZ_LOCAL.lower():
            timestamp = timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)
        eventType = jobj["common"]["type"]
        img: GImage = None
        candidates: List[Candidate] = []
        if CONFIG.STORE_IMAGE and jobj["images"]:
            # nf todo - what about a scene with multiple people, how does Gorilla send that?
            for iobj in jobj["images"]:
                if CONFIG.STORE_IMAGE_KIND in iobj["type"]:
                    if "dataBase64" in iobj and iobj["dataBase64"]:
                        img = GImage(iobj["dataType"], iobj["dataFileName"], iobj["dataBase64"])
                    else:
                        print(f"Image field was unavailable for gorilla event id: {id}")
                        img = None
        if "fr" in jobj and jobj["fr"]:
            if jobj["fr"]["candidates"]:
                for c in jobj["fr"]["candidates"]:
                    score = c["similiarityScore"]
                    try:
                        score = float(score) # scores are a number in range of [0,1]
                    except:
                        print("Failed to get score for candidate, likely was an error string, and not a float")
                        score = None # failed to convert to a number because what was received was likely an error string. Set default to None
                    cand = Candidate(c["id"], c["displayName"], score)
                    candidates.append(cand)
        else:
            print(f"fr data field was unavailable for gorilla event id: {id}")
        candidate: Candidate = candidates[0] if candidates else None
        update_bap(candidates)
        update_ivar(id, timestamp, eventType, img, candidate, json.dumps(jobj) if CONFIG.STORE_FULL_JSON else None)
        return 0
    except Exception as e:
        raise RuntimeError("Failed to store Gorilla data", e)

def main():
    print("call form LibEllen")
    print("Settign the backing store")
    SetActiveStore(STORE_XLS)
    print(f"Backing store set to {_CHOSEN_STORE}")
    InitBackingStore()
    print("Running test to backing")
    ACTIVE_STORE.main()
    #test_blobs()
    return 0

def test_blobs():
    with open('./data/unknown_person.json') as f:
        j = json.load(f)
    receive_json(j)
    with open("./data/known_person.json") as f:
        j = json.load(f)
    receive_json(j)

if __name__ == "__main__":
    sys.exit(main())