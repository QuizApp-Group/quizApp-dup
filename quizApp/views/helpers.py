"""Various functions that are useful in multiple views.
"""
import base64
import random

from flask import abort, jsonify
from flask_security import current_user
from sqlalchemy.orm.exc import NoResultFound

from quizApp import models
from quizApp import db


def get_or_create_assignment_set(experiment):
    """Attempt to retrieve the AssignmentSet record for the current
    user in the given Experiment.

    If no such record exists, grab a random AssignmentSet record in the
    experiment AssignmentSet pool, copy it to be the current user's
    AssignmentSet record, and return that.
    """
    try:
        assignment_set = models.AssignmentSet.query.\
            filter_by(participant_id=current_user.id).\
            filter_by(experiment_id=experiment.id).one()
    except NoResultFound:
        pool = models.AssignmentSet.query.\
            filter_by(participant_id=None).\
            filter_by(experiment_id=experiment.id).all()
        try:
            assignment_set = random.choice(pool)
        except IndexError:
            return None
        assignment_set.participant = current_user
        db.session.commit()

    return assignment_set


def get_first_assignment(experiment):
    """Get the first assignment for this user in this experiment.

    Note that this is not necessarily the same as the first assignment in an
    assignment set. This function will first call
    ``get_or_create_assignment_set`` in order to retrieve an assignment set.
    If there is no assignment set or it is empty, this function returns none.

    If the set is complete, this function returns the first assignment in the
    set.
    """
    assignment_set = get_or_create_assignment_set(experiment)

    if not assignment_set:
        assignment = None
    elif len(assignment_set.assignments) == 0:
        assignment = None
    elif assignment_set.complete:
        assignment = assignment_set.assignments[0]
    else:
        try:
            assignment = assignment_set.\
                assignments[assignment_set.progress]
        except IndexError:
            assignment = assignment_set.assignments[0]
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


def experiment_to_url_code(experiment):
    """Convert this experiment to a key that we can use to look it up later.

    Not much trickery going on, but unless a participant knows the name of the
    experiment as well as its ID they can't find it.
    """
    code_string = u"{}-{}".format(experiment.id, experiment.name[:10])
    code = base64.urlsafe_b64encode(code_string.encode())
    return code.decode("utf-8")


def url_code_to_experiment(code):
    """Return the experiment referreed to by this key.
    """
    decoded = base64.urlsafe_b64decode(code.encode("utf8")).decode("utf-8")
    id_part = decoded.split("-", 1)[0]
    experiment = validate_model_id(models.Experiment, id_part)

    if experiment_to_url_code(experiment) != code:
        abort(404)

    return experiment
