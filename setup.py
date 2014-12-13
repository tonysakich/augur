#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="augur",
    version="0.2.1",
    description="decentralized prediction markets",
    author="Scott Leonard, Jack Peterson, Chris Calderon",
    author_email="<team@augur.net>",
    maintainer="Scott Leonard",
    maintainer_email="<scott@augur.net>",
    license="MIT",
    url="https://github.com/AugurProject/augur",
    download_url = "https://github.com/AugurProject/augur/tarball/0.2.1",
    packages=["augur"],
    install_requires=["Flask", "Flask-SocketIO", "GitPython", "Jinja2", "Werkzeug", "MarkupSafe", "gevent", "gitdb", "greenlet", "itsdangerous", "smmap", "numpy", "six"],
    keywords = ["bitcoin", "truthcoin", "prediction markets", "forecasting", "decentralized"]
)
