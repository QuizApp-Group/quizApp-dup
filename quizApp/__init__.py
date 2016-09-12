"""Handle creating the app and configuring it.
"""
from __future__ import print_function
from __future__ import unicode_literals
import pdb
from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.signals import user_registered
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect

from quizApp import config


db = SQLAlchemy()
csrf = CsrfProtect()
security = Security()
migrate = Migrate()
mail = Mail()


def create_app(config_name, overrides=None):
    """Create and return an instance of this application.
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(config.configs[config_name])
    app.config.from_pyfile("instance_config.py", silent=True)
    if overrides:
        app.config.from_mapping(overrides)

    print("Using config: " + config_name)

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    from quizApp.models import User, Role
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)
    # Workaround for flask-security bug #383
    security.datastore = user_datastore
    security.app = app

    migrate.init_app(app, db)

    from quizApp.views.activities import activities
    from quizApp.views.core import core
    from quizApp.views.datasets import datasets
    from quizApp.views.experiments import experiments
    from quizApp.views.data import data
    from quizApp.views.mturk import mturk
    from quizApp.filters import filters

    app.register_blueprint(activities)
    app.register_blueprint(data)
    app.register_blueprint(core)
    app.register_blueprint(datasets)
    app.register_blueprint(experiments)
    app.register_blueprint(mturk)
    app.register_blueprint(filters)

    user_registered.connect(apply_default_user_role, app)

    return app


def apply_default_user_role(_, user, **__):
    """When a new user is registered, make them a participant.
    """
    user.type = "participant"
    security.datastore.add_role_to_user(user, "participant")
    db.session.commit()
