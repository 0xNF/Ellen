# Ellen

This project is a webserver that receives events from Gorilla IVAR into a Sqlite Database.

Because we are saving Gorilla data, the namesake is from The Ellen Fund, whose mission is to save real-life gorillas.

# Quick Install
1. Install Python3.8 from the [Windows Store](https://www.microsoft.com/en-us/p/python-38/9mssztt1n39l?activetab=pivot:overviewtab)
1. Download the zip `ellen.zip`
1. extract anywhere
1. open `ellen/`
1. run `install.bat`
1. optional auto-start:  
    1. make a shortcut to `ellen_windows_store.bat`
    1. move the shortcut to `shell:startup`
1. run `ellen_windows_store.bat`


# Installation via Source

For use with `libellenxls`, ensure that the following two libraries are installed:
* https://openpyxl.readthedocs.io/en/stable/
* https://pypi.org/project/Pillow/

```bash
pip install pillow
pip install openpyxl
pip install flask
```

# Usage - Server
Start:
```bash
./src/server.py
```

# Configuration
The `config.ini` file is supplied by default. In case it is deleted, it will be regenerated.  
The configuration has the following options available:
```
maxkeepdays = 30        // Maximum number of days back to keep recorded data
maxrecordcount = 10000  // Maximum number of records to keep
maxdbsize = 100         // Maximum size of the storage file
storeimagekind = FACE   // Type of Gorilla Image data to save [FACE, OBJECT, SCENE]
storeimage = True       // Whether to store Gorilla Image data at all [True, False]
storefulljson = False   // Whether to store the entire Gorilla Data Object [True, False]
datadirectory = ./data  // Where to store temporary data
outputdirectory = ./    // Where to output the Storage file
kind = XLS              // Storage File type in either an Excel spreadsheet, or a Sqlite file [XLS, SQL]
```

This config can be reloaded at any time with the `/reload` endpoint.

## Endpoints:
* /savegorilla
    - POST
    - Receives Gorilla data in JSON format from the IVAR server. 
* /healthcheck
    - GET
    - Returns if the server is running
* /reload
    - GET
    - Reloads the config at `./config.ini` without requiring a server restart

| Becuase we rely on some private methods to better manipulate Image positions, please use `openpyxl version 3.0.4`. 

- nice-to-have:
    - wtf is going on with python module imports, holy fuck fix it later