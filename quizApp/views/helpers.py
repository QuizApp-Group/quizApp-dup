"""Various functions that are useful in multiple views.
"""
import random
from flask import abort, jsonify
from flask_security import current_user
from sqlalchemy.orm.exc import NoResultFound

from quizApp import models
from quizApp import db


def get_or_create_participant_experiment(experiment):
    """Attempt to retrieve the ParticipantExperiment record for the current
    user in the given Experiment.

    If no such record exists, grab a random ParticipantExperiment record in the
    experiment ParticipantExperiment pool, copy it to be the current user's
    ParticipantExperiment record, and return that.
    """
    try:
        participant_experiment = models.ParticipantExperiment.query.\
            filter_by(participant_id=current_user.id).\
            filter_by(experiment_id=experiment.id).one()
    except NoResultFound:
        pool = models.ParticipantExperiment.query.\
            filter_by(participant_id=None).\
            filter_by(experiment_id=experiment.id).all()
        try:
            participant_experiment = random.choice(pool)
        except IndexError:
            return None
        participant_experiment.participant = current_user
        db.session.commit()

    return participant_experiment


def get_first_assignment(experiment):
    """Get the first assignment for this user in this experiment.
    """
    participant_experiment = get_or_create_participant_experiment(experiment)
    if not participant_experiment:
        assignment = None
    elif len(participant_experiment.assignments) == 0:
        assignment = None
    else:
        assignment = participant_experiment.assignments[0]
    return assignment


def validate_model_id(model, model_id, code=404):
    """Given a model and id, retrieve and return that model from the database
    or abort with the given code.
    """
    obj = model.query.get(model_id)

    if not obj:
        abort(code)

    return obj


def validate_form_or_error(form):
    """Validate this form or return errors in JSON format.

    If the form is valid, None is returned.
    """
    if not form.validate():
        return jsonify({"success": 0, "errors": form.errors})

    return None
