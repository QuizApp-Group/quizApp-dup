"""Handle creating the app and configuring it.
"""
from __future__ import print_function
from __future__ import unicode_literals
from sqlalchemy import event
from marshmallow_sqlalchemy import ModelConversionError, ModelSchema

from flask import Flask
from flask_jwt import JWT
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.signals import user_registered
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect

from quizApp import config


db = SQLAlchemy()
csrf = CsrfProtect()
security = Security()
migrate = Migrate()
jwt = JWT()
restful = Api(prefix="/api", decorators=[csrf.exempt])
ma = Marshmallow()
mail = Mail()


def create_app(config_name, overrides=None):
    """Create and return an instance of this application.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Set the config
    app.config.from_object(config.configs[config_name])
    app.config.from_pyfile("instance_config.py", silent=True)
    if overrides:
        app.config.from_mapping(overrides)

    print("Using config: " + config_name)
    from quizApp import models
    event.listen(db.mapper, 'after_configured', setup_schema(models.Base))

    db.init_app(app)  # flask-sqlalchemy
    csrf.init_app(app)  # CSRF for wtforms
    ma.init_app(app)  # flask-marshmallow
    migrate.init_app(app, db)  # flask-migrate
    mail.init_app(app)

    # Initialize flask-restful
    from quizApp import resources
    restful.init_app(app)

    # Initialize flask-security
    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(app, user_datastore)
    # Workaround for flask-security bug #383
    security.datastore = user_datastore
    security.app = app
    ma.init_app(app)

    # Register all necessary blueprints
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


def setup_schema(Base):
    """Create a function which incorporates the Base and session information
    """
    def setup_schema_fn():
        """Attach a marshmallow schema to every db model
        """
        for class_ in Base._decl_class_registry.values():
            if hasattr(class_, '__tablename__'):
                if class_.__name__.endswith('Schema'):
                    raise ModelConversionError(
                        "For safety, setup_schema can not be used when a"
                        "Model class ends with 'Schema'"
                    )

                class Meta(object):
                    """Meta information for the schema.
                    """
                    model = class_

                schema_class_name = '%sSchema' % class_.__name__

                schema_class = type(
                    str(schema_class_name),
                    (ModelSchema,),
                    {'Meta': Meta}
                )

                setattr(class_, '__marshmallow__', schema_class)

    return setup_schema_fn


def apply_default_user_role(_, user, **__):
    """When a new user is registered, make them a participant.
    """
    user.type = "participant"
    security.datastore.add_role_to_user(user, "participant")
    db.session.commit()
