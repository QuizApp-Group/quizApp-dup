"""Handle creating the app and configuring it.
"""
from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from quizApp import config


db = SQLAlchemy()
csrf = CsrfProtect()
security = Security()


def create_app(config_name, overrides=None):
    """Create and return an instance of this application.
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(config.configs[config_name])
    app.config.from_pyfile("instance_config.py", silent=True)
    if overrides:
        app.config.from_mapping(overrides)

    print "Using config: " + config_name

    db.init_app(app)
    csrf.init_app(app)

    from quizApp.models import User, Role
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)
    # Workaround for flask-security bug #383
    security.datastore = user_datastore
    security.app = app

    from quizApp.views.activities import activities
    from quizApp.views.core import core
    from quizApp.views.datasets import datasets
    from quizApp.views.experiments import experiments
    from quizApp.views.mturk import mturk

    app.register_blueprint(activities)
    app.register_blueprint(core)
    app.register_blueprint(datasets)
    app.register_blueprint(experiments)
    app.register_blueprint(mturk)

    return app
