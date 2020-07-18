# Ellen

This project is a webserver that receives events from Gorilla IVAR into either an `.xlsx` excel file or a `.sqlite` Sqlite Database.

Because we are saving Gorilla data, the namesake is from [The Ellen Fund](https://theellenfund.org/gorillas), whose mission is to save real-life gorillas.

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

# build a single-file-exe
We use [Pyinstaller](https://www.pyinstaller.org/). It cannot be used with Windows Store python due to permission errors to the AppData folder.

This process was tested with Windows python `Python 3.8.4`.
```
pip install pyinstaller
```
build single file exe:
we take `$ellen_source` to be the top-level ellen directory.
```
cd $ellen_source
pyinstaller --onefile .\src\server.py --hidden-import=pkg_resources.py2_warn --add-data "./src/lib;lib"
```
omitting the `--hidden-import` flag will cause errors.


# Installation via Source

For use with `libellenxls`, ensure that the following two libraries are installed:
* https://openpyxl.readthedocs.io/en/stable/
* https://pypi.org/project/Pillow/

```bash
pip install pillow
pip install openpyxl
pip install flask
```

| Becuase we rely on some private methods to better manipulate Image positions, please use `openpyxl version 3.0.4`. 

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
maxdbsize = 100         // Maximum size of the storage file in MB
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

## Todo
- nice-to-have:
    - wtf is going on with python module imports?
    - cleanup old methods
    - make better installation method
    