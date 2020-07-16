# Ellen

This project is a webserver that receives events from Gorilla IVAR into a Sqlite Database.

Because we are saving Gorilla data, the namesake is from The Ellen Fund, whose mission is to save real-life gorillas.

# Installation

For use with `libellenxls`, ensure that the following two libraries are installed:
* https://openpyxl.readthedocs.io/en/stable/
* https://pypi.org/project/Pillow/

```bash
pip install pillow
pip install openpyxl
```

| Becuase we rely on some private methods to better manipulate Image positions, please use `openpyxl version 3.0.4`. 
# TODO
- Prune XLS data
    - delete old images
    - move image anchor
- Better File configuration
    - config.ini  
        max_save_days=2  
        etc...
- Ellen_Server
    - receive Gorilla Post