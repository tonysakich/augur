## Augur-UI

### Requirements

- Python 2.7
- [Truthcoin-POW](https://github.com/zack-bitcoin/Truthcoin-POW)
- Flask
- Flask-SocketIO

### Installation

#### *nix
- checkout Augur-UI next to Truthcoin-POW (or change config path in app.py)
- $ cd Augur-UI
- $ pip install -r requirements.txt
- $ python app.py
- http://localhost:9000

#### Windows
Windows installation is a quite bit more involved than any *nix platform. Here are some steps:

1. First make sure you have [python installed](https://www.python.org/downloads/release/python-278/). Also, make sure that you have downloaded [Truthcoin-POW](https://github.com/zack-bitcoin/Truthcoin-POW). This and Truthcoin-UI will have to be extracted to the same directory if you download the zip files. 
2. You need to install a few dependencies, namely numpy, six, cdecimal and pip, which can all be found [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/). I recommend using Ctrl+F to find them (and make sure you get the newest one that matches your python installation's architecture!)
3. Once those are installed, you need to download [ez_setup.py](https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py) (right click on the link and click "Save Target As" and save with the name ez_setup.py.) You should be able to double click this file if you have installed python, and it will run and close on it's own. 
4. Now you need to edit the `Path` environment variable. To do this, go to the `Start menu`, right click on `Computer`, click on `Advanced System Settings` in the upper left, click `Environment Variables` in the bottom right, then in the `System Variables` section, scroll down till you see `Path`. Click on `Path`, and click `Edit...`. Press the `Home` key to get to the start of the line, then add `C:\Python27\Scripts;C:\Python27\;` to the start of the line and click `OK`. 
5. Now go to http://aka.ms/vcpython27 to download and install the windows C compiler for use with pip.
6. Finally, go back to the `Start Menu` type `cmd` and press `Enter`, then type `pip install flask flask-socketio`. 

You can run the UI by double clicking on `app.py`.
