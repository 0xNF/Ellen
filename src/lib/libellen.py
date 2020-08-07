from typing import List, Set, Dict, Tuple, Optional
import sys, os
import sqlite3
import json
import configparser
from datetime import datetime, time, timedelta
from .libellen_xls import prune_old_data as prune_xls, ensure as ensure_xls, update_bap as update_bap_xls, update_ivar as update_ivar_xls, set_config as set_config_xls
from .libellen_sql import prune_old_data as prune_sql, ensure as ensure_sql, update_bap as update_bap_sql, update_ivar as update_ivar_sql, set_config as set_config_sql
from .libellen_core import Config, Candidate, GImage

# If true, stores the entire JSON blob as sent by the IVAR server. This will increase DB size.
STORE_FULL_JSON = False

# If true, stores the b64 encoded image data for the associated Ivar event. This will increase DB size.
STORE_IMAGE = True

# Multiple image types are sent by Gorilla - this determines which one to save
# available choices are:
    # SCENE, OBJECT, THUMB, FACE
# Suggested storage kind of FACE, as it is smallest
STORE_IMAGE_KIND = "FACE"

# Maximum size of the Database in Megabytes.
# numebrs <= 0 are considered to be 'unlimited'
MAX_DB_SIZE = 100

# Maximium number of records to keep before we start dropping the earliest recorded record
# any number <= 0 is considerwed to be 'unlimited'
MAX_RECORD_COUNT = 10_000

# Maximium number of days backwards in time to keep records before we start deleting
# any number <= 0 is considered to be 'unlimited'
MAX_KEEP_DAYS = 30

# Where to store temporary items like Images sent from Gorilla
DATA_DIR = "./"

# Where to write the sql or xls files
OUTPUT_DIR = "./"

# What type to output data to [XLS or SQL]
KIND = "XLS"

STORE_XLS = "XLS"
STORE_SQL = "SQL"

CONFIG: Config = Config(STORE_FULL_JSON, STORE_IMAGE, STORE_IMAGE_KIND, MAX_DB_SIZE, MAX_RECORD_COUNT, MAX_KEEP_DAYS, DATA_DIR, OUTPUT_DIR, STORE_XLS)


_CHOSEN_STORE = None # assigned with the values from either STORE_XLS or STORE_SQL
ACTIVE_STORE = None

prune = None
ensure = None
update_bap = None
update_ivar = None
set_config = None

def read_config() -> Config:
    """ reads the config file at the regular path, returns None if no config is found """
    global CONFIG, MAX_DB_SIZE, MAX_KEEP_DAYS, MAX_RECORD_COUNT, STORE_IMAGE_KIND, STORE_IMAGE, STORE_FULL_JSON, DATA_DIR, OUTPUT_DIR, KIND
    conf = configparser.ConfigParser()
    if not conf.read("./config.ini"):
        return None
    try:
        MAX_KEEP_DAYS = int(conf["DEFAULT"]["MaxKeepDays"])
        MAX_RECORD_COUNT = int(conf["DEFAULT"]["MaxRecordCount"])
        MAX_DB_SIZE = int(conf["DEFAULT"]["MaxDbSize"])
        STORE_IMAGE = bool(conf["DEFAULT"]["StoreImage"])
        STORE_IMAGE_KIND = str(conf["DEFAULT"]["StoreImageKind"])
        STORE_FULL_JSON = bool(conf["DEFAULT"]["StoreFullJson"])
        DATA_DIR = str(conf["DEFAULT"]["DataDirectory"])
        OUTPUT_DIR = str(conf["DEFAULT"]["OutputDirectory"])
        KIND = str(conf["DEFAULT"]["Kind"])
        CONFIG = Config(STORE_FULL_JSON, STORE_IMAGE, STORE_IMAGE_KIND, MAX_DB_SIZE, MAX_RECORD_COUNT, MAX_KEEP_DAYS, DATA_DIR, OUTPUT_DIR, KIND)
        return CONFIG
    except:
        return None

def write_default_config() -> Config:
    """ creates a default Config.ini at the regular path and returns the config object """
    conf = configparser.ConfigParser()
    conf["DEFAULT"] = {
        "MaxKeepDays": '30',
        "MaxRecordCount": "10000",
        "MaxDbSize": "100",
        "StoreImageKind": "FACE",
        "StoreImage": "True",
        "StoreFullJson": "False",
        "DataDirectory": "./data",
        "OutputDirectory": "./",
        "Kind": "XLS"
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

def SetActiveStore(which: str):
    """ Sets the backing store to use. Accepted values are either XLS or SQL """
    global ACTIVE_STORE, _CHOSEN_STORE, prune, ensure, update_bap, update_ivar
    if which == STORE_XLS:
        prune = prune_xls
        ensure = ensure_xls
        update_bap = update_bap_xls
        update_ivar = update_ivar_xls
        set_config = set_config_xls
        # ACTIVE_STORE = libellen_xls
    elif which == STORE_SQL:
        prune = prune_sql
        ensure = ensure_sql
        update_bap = update_bap_sql
        update_ivar = update_ivar_sql
        set_config = set_config_sql
        # ACTIVE_STORE = libellen_sql
    else:
        raise Exception("Backing store must be oneof 'XLS', 'SQL'")
    _CHOSEN_STORE = which
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

# def prune() -> int:
#     """ using the current Active Store, prune the data according to Config Rules so that the files don't get too unwiedly.
#      Returns the number of entries deleted. """
#     return prune_old_data()

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