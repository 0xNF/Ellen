from typing import List, Set, Dict, Tuple, Optional
import sys, os
import sqlite3
import json
from datetime import datetime, time, timedelta
import libellen_sql
import libellen_xls
from libellen_core import Config, Candidate, GImage

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
MAX_RECORD_COUNT = 2

# Maximium number of days backwards in time to keep records before we start deleting
# any number <= 0 is considered to be 'unlimited'
MAX_KEEP_DAYS = 30

CONFIG: Config = Config(STORE_FULL_JSON, STORE_IMAGE, STORE_IMAGE_KIND, MAX_DB_SIZE, MAX_RECORD_COUNT, MAX_KEEP_DAYS, "./data")

STORE_XLS = "XLS"
STORE_SQL = "SQL"

_CHOSEN_STORE = None # assigned with the values from either STORE_XLS or STORE_SQL
ACTIVE_STORE = None

def InitBackingStore():
    """ Initializes the backing store and ensures it is in a writable state """
    if ACTIVE_STORE is not None:
        ACTIVE_STORE.ensure() # dynamic dispatch to the true storage's ensure method
    else:
        raise Exception("No Active Store was set. Call SetActiveStore before continuing")
    return

def SetActiveStore(which: str):
    """ Sets the backing store to use. Accepted values are either XLS or SQL """
    global ACTIVE_STORE, _CHOSEN_STORE
    if which is STORE_XLS:
        ACTIVE_STORE = libellen_xls
    elif which is STORE_SQL:
        ACTIVE_STORE = libellen_sql
    else:
        raise Exception("Backing store must be oneof 'XLS', 'SQL'")
    _CHOSEN_STORE = which
    ACTIVE_STORE.set_config(CONFIG)
    return

def receive_json(jobj: dict):
    """ given an ivar event, updates the data storage with the received data, according to the storage preferences """
    id = jobj["id"]
    timestamp = datetime.strptime(jobj["common"]["time"], "%Y-%m-%dT%H:%M:%S.%fZ")
    eventType = jobj["common"]["type"]
    img: GImage = None
    candidates: List[Candidate] = []
    if CONFIG.STORE_IMAGE and jobj["images"]:
        # nf todo - what about a scene with multiple people, how does Gorilla send that?
        for iobj in jobj["images"]:
            if CONFIG.STORE_IMAGE_KIND in iobj["type"]:
                if iobj["dataBase64"]:
                    img = GImage(iobj["dataType"], iobj["dataFileName"], iobj["dataBase64"])
                else:
                    print(f"Image field dataBase64 was unavailable for gorilla event id: {id}")
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
    ACTIVE_STORE.update_bap(candidates)
    ACTIVE_STORE.update_ivar(id, timestamp, eventType, img, candidate, json.dumps(jobj) if CONFIG.STORE_FULL_JSON else None)
    return

def prune() -> int:
    """ using the current Active Store, prune the data according to Config Rules so that the files don't get too unwiedly.
     Returns the number of entries deleted. """
    return ACTIVE_STORE.prune_old_data()

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