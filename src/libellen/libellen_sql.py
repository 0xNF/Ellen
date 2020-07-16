from typing import List, Set, Dict, Tuple, Optional
import sys, os
import sqlite3
import json
from datetime import datetime, time, timedelta
from libellen_core import Config, Candidate, GImage
## Configuration Data related to Ellen's functioning
# Path to the Database where we store our seen items
DBPath = "./ellen.sqlite"

# Private Connection to the Database - we keep it open whenever we can
_CONN: sqlite3.Connection = None
CONFIG: Config = None

def _open_conn() -> bool:
    """Opens the connection to the database, and stores it in _CONN. Returns whether the connection was successful"""
    global _CONN
    if _CONN is None:
        _CONN = sqlite3.connect(DBPath)
        return _CONN is not None
    return True

def _check_db_exists() -> bool:
    """Checks that the Sqlite DB exits"""
    if not os.path.isfile(DBPath):
        return False
    try:
        return _open_conn()
    except:
        _remove_old_db()
        return False

def _remove_old_db() -> None:
    """removes any invalid or corrupt db file we had for whatever reason. """
    try:
        print(f"Removing old db at {DBPath}")
        os.remove(DBPath)
        return
    except FileNotFoundError:
        return
    except Exception as e:
        print(f"Failed to remove file at: {DBPath}: {e}")
        raise e

def _establish_new_db() -> bool:
    """creates our tables and layout in a new DB file """
    _open_conn()
    c = _CONN.cursor()
    
    # create the BapId table - we store People/Candidates here
    sql = """CREATE TABLE IF NOT EXISTS "bapdata" (
        "Id"    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "BapId" INTEGER NOT NULL UNIQUE,
        "PersonName"    TEXT
    );"""
    c.execute(sql)
    
    # create the IvarData table - we store seen Ivar events here
    sql = """
    CREATE TABLE IF NOT EXISTS "ivardata" (
        "Id"    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "GorillaId"	TEXT UNIQUE NOT NULL,
        "Timestamp" INTEGER NOT NULL,
        "EventType" TEXT NOT NULL,
        "PersonId"  INTEGER,
        "Confidence"    INTEGER,
        "ImageData" BLOB,
        "FullBlob"  BLOB,
        FOREIGN KEY("PersonId") REFERENCES "bapdata"("BapId")
    );
    """
    c.execute(sql)
    c.close()
    _CONN.commit()
    return True

def _ensure_db() -> bool:
    """Ensures that our DB exists, and creates a new one if not"""
    if not _check_db_exists():
        return _establish_new_db()
    return False

def ensure() -> bool:
    return _ensure_db()

def set_config(config: Config):
    global CONFIG
    CONFIG = config
    return

def prune_old_data() -> int:
    """Checks various conditions, like max_rows, max_date, etc, in the DB and prunes any data that qualifies. Returns the number of records expunged. """
    _open_conn()
    c = _CONN.cursor()
    
    rowcount = c.execute("SELECT COUNT(*) FROM ivardata").fetchone()[0]
    # Check for number of rows beyond max row count
    excess_rows = rowcount - CONFIG.MAX_RECORD_COUNT
    if excess_rows > 0:
            c.execute("Delete from ivardata where rowid IN (Select rowid from ivardata limit ?);", (excess_rows,))

    # Check for items older than max keep days:
    maxDate = datetime.now() - timedelta(days=CONFIG.MAX_KEEP_DAYS)
    rows = c.execute("DELETE FROM ivardata WHERE Timestamp <= ?", (maxDate, ))

    new_rowcount = c.execute("SELECT COUNT(*) FROM ivardata").fetchone()[0]
    c.close()
    _CONN.commit()
    return rowcount - new_rowcount


def update_bap(candidates: List[Candidate]):
    """ given a list of potential candidate matches, update the bap table to ensure that any new known people are properly inserted"""
    _open_conn()
    c = _CONN.cursor()

    sql = "INSERT OR IGNORE INTO bapdata (BapId, PersonName) VALUES (?,?);"
    ins = [(x.Id, x.DisplayName,) for x in candidates] 
    c.executemany(sql, ins)
    c.close()
    _CONN.commit()
    return

def update_ivar(gorillaId: str, timestamp: datetime, eventType: str, img: GImage, candidate: Candidate, jobj: str):
    """ Inserts data into the Ivar table. """
    _open_conn()
    c = _CONN.cursor()

    sql = "INSERT INTO ivardata (GorillaId, Timestamp, EventType, PersonId, Confidence, ImageData, FullBlob) VALUES (?,?,?,?,?,?,?);"
    pid = candidate.Id if candidate else None
    score = candidate.SimiliarityScore if candidate else None
    imgb64 = img.B64 if img else None
    c.execute(sql, (gorillaId, timestamp, eventType, pid, score, imgb64, jobj,))
    c.close()
    _CONN.commit()
    return


def main():
    print("lib_elen_SQL:")
    print(f"Checking {DBPath} exists: {_check_db_exists()}")
    print("Ensuring DB creation...")
    _ensure_db()
    print("Pruning old data")
    pruned = prune_old_data()
    print(f"Pruned {pruned} old rows")
    return 0

if __name__ == "__main__":
    sys.exit(main())