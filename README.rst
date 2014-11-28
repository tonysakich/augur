augur: decentralized prediction markets
---------------------------------------

.. image:: https://travis-ci.org/AugurProject/augur.svg
    :target: https://travis-ci.org/AugurProject/augur

.. image:: https://coveralls.io/repos/tensorjack/augur/badge.png
  :target: https://coveralls.io/r/tensorjack/augur

.. image:: https://badge.fury.io/py/augur.svg
    :target: http://badge.fury.io/py/augur

This is the Augur prototype.  It is currently in alpha testing.  Our installation procedures and other documentation will get better/easier as time goes on and we smooth out the rough edges!  In the meantime, please `email <mailto:team@augur.net>`__ us or join us in `#augur <irc://irc.freenode.net/augur>`__ on FreeNode IRC if you have trouble installing or running the prototype.

Caution: the prototype is built for rapid testing.  We don't guarantee its security or scalability!  Use at your own risk :)

Requirements
~~~~~~~~~~~~

-  Python 2.7
-  git
-  pip

Installation
~~~~~~~~~~~~

MacOS X
^^^^^^^

First, install `Xcode command line tools <https://developer.apple.com/downloads/>`__. Then enter the
following commands in the terminal:

::

    $ git clone https://github.com/AugurProject/Augur-UI.git
    $ cd Augur-UI
    $ sudo pip install -r requirements.txt

Start the Augur client using ``augur_ctl``:

::

    $ ./augur_ctl start


Linux (Ubuntu)
^^^^^^^^^^^^^^

So far, we have only tested Augur-UI on Ubuntu 12.04/14.04.  If you've tested this on another Linux distro, `let us know <mailto:team@augur.net>`__!

First, you will need to install a few background packages using ``apt-get``:

::

    $ apt-get install git libpython-dev python-numpy
    $ pip2 install m3-cdecimal

    $ git clone https://github.com/AugurProject/Augur-UI.git
    $ cd Augur-UI
    $ pip install -r requirements.txt

Start the Augur client using ``augur_ctl``:

::

    $ ./augur_ctl start


Windows
^^^^^^^

Installing the prototype on Windows requires a few extra steps:

1. First make sure you have `Python installed <https://www.python.org/downloads/release/python-278/>`__.

2. You need to install a few dependencies: numpy, six, cdecimal and pip, which can all be found `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`__.  I recommend using Ctrl+F to find them.  Make sure you get the newest one that matches your Python installation's architecture!

3. Once those are installed, you need to download `ez\_setup.py <https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py>`__ (right click on the link and click "Save Target As" and save with the name ez\_setup.py.) You should be able to double click this file if you have installed Python, and it will run and close on its own.

4. Now you need to edit the ``Path`` environment variable. To do this, go to the ``Start menu``, right click on ``Computer``, click on ``Advanced System Settings`` in the upper left, click ``Environment Variables`` in the bottom right, then in the ``System Variables`` section, scroll down till you see ``Path``. Click on ``Path``, and click ``Edit...``. Press the ``Home`` key to get to the start of the line, then add ``C:\Python27\Scripts;C:\Python27\;`` to the start of the line and click ``OK``.

5. Now go to http://aka.ms/vcpython27 to download and install the windows C compiler for use with pip.

6. Finally, go back to the ``Start Menu`` type ``cmd`` and press ``Enter``, then type ``pip install flask flask-socketio``.

You can run Augur-UI by going into the ``ui`` directory and double-clicking on ``app.py``.

Usage
~~~~~

Once Augur is installed, navigate to ``http://localhost:9000`` in your web browser, and you should see the Augur interface.  To fire up your local node, click the red "Node stopped" button, then "Start node".  After your node starts, you will see the main Augur interface.