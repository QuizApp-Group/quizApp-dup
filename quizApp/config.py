"""Configurations for the project. These are loaded in app.py.
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """Global default config.
    """

    WTF_CSRF_ENABLED = True
    DEBUG = False
    TESTING = False
    SECRET_KEY = "---"
    WTF_CSRF_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXPERIMENTS_PLACEHOLDER_GRAPH = "missing.png"
    SECURITY_REGISTERABLE = True


class Production(Config):
    """Configuration for production environments.
    """
    DEBUG = False
    TESTING = False
    # SECURITY_PASSWORD_HASH = "bcrypt"


class Development(Config):
    """Configuration for development environments.
    """
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://quizapp:foobar@localhost/quizapp"
    SECRET_KEY = "Foobar"
    SECURITY_SEND_REGISTER_EMAIL = False
    SQLALCHEMY_ECHO = True


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
