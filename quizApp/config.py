"""Configurations for the project. These are loaded in
app.py.
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """Global default config.
    """

    WTF_CSRF_ENABLED = True
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = True
    SECRET_KEY = "---"
    WTF_CSRF_METHODS=["POST","PUT","PATCH","DELETE"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Production(Config):
    """Configuration for production environments.
    """
    DEBUG = False
    TESTING = False

class Development(Config):
    """Configuration for development environments.
    """
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://quizapp:foobar@localhost/quizapp"
    SECRET_KEY = "Foobar"

class Testing(Config):
    """Config used for testing.
    """
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://quizapp:foobar@localhost/quizapp_test"
    SECRET_KEY = "Foobar"

configs = {
    "production": Production,
    "development": Development,
    "testing": Testing,
}
