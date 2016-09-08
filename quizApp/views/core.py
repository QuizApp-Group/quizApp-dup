"""This blueprint takes care of rendering static pages outside of the other
blueprints.
"""
import random
import uuid
import string

from flask import Blueprint, render_template, redirect, url_for, request,\
    redirect
from flask_security import roles_required, login_required, current_user,\
    login_user
from flask_security.utils import encrypt_password

from quizApp import models, db, security

core = Blueprint("core", __name__, url_prefix="/")


# homepage
@core.route('')
def home():
    """Display the homepage."""
    return render_template('core/index.html',
                           is_home=True)


def query_exists(query):
    """Given a query, return True if it would return any rows, and False
    otherwise.
    """
    return db.session.query(query.exists()).scalar()


@core.route("getting_started", methods=["GET"])
@roles_required("experimenter")
def getting_started():
    """Show some instructions for getting started with quizApp.
    """
    experiments_done = query_exists(models.Experiment.query)
    activities_done = query_exists(models.Activity.query)
    datasets_done = query_exists(models.Dataset.query)
    media_items_done = query_exists(models.MediaItem.query)
    assignments_done = query_exists(models.Assignment.query)

    return render_template("core/getting_started.html",
                           experiments_done=experiments_done,
                           activities_done=activities_done,
                           datasets_done=datasets_done,
                           media_items_done=media_items_done,
                           assignments_done=assignments_done)


@core.route("post_login", methods=["GET"])
@login_required
def post_login():
    """Once a user has logged in, redirect them based on their role.
    """
    if current_user.has_role("experimenter"):
        return redirect(url_for("core.getting_started"))
    else:
        return redirect(url_for("experiments.experiments"))


@core.route("auto_register", methods=["GET"])
def auto_register():
    """Convenience endpoint for using QuizApp embedded in another site.

    When a logged in user accesses this endpoint, they will be redirected to
    the specified experiment.

    When a user that is not logged in access this endpoint, an account will be
    created, they will be logged in, then redirected to the specified
    experiment.
    """
    if not current_user.is_authenticated:
        password = ''.join(random.SystemRandom().
                           choice(string.ascii_uppercase + string.digits)
                           for _ in range(0, 15))
        participant = models.Participant(
            email=str(uuid.uuid4()),  # just give them a random email
            password=encrypt_password(password))
        security.datastore.add_role_to_user(participant, "participant")
        security.datastore.activate_user(participant)
        participant.save()
        login_user(participant)

    return redirect(url_for("experiments.experiment",
                   experiment_id=request.args["experiment_id"]))
