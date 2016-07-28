"""Views that handle CRUD for experiments and rendering questions for
participants.
"""
from collections import defaultdict
from datetime import datetime
import json
import os

import openpyxl
from flask import Blueprint, render_template, url_for, jsonify, abort, \
    current_app, request
from flask_security import login_required, current_user, roles_required
from sqlalchemy.orm.exc import NoResultFound

from quizApp import db
from quizApp.forms.common import DeleteObjectForm
from quizApp.forms.experiments import CreateExperimentForm, \
    get_question_form, ImportAssignmentForm
from quizApp.models import Choice, Experiment, Assignment, \
    ParticipantExperiment, Activity, Participant
from quizApp.views.helpers import validate_model_id
from quizApp.views import import_export

experiments = Blueprint("experiments", __name__, url_prefix="/experiments")

EXPERIMENT_ROUTE = "/<int:experiment_id>"
ASSIGNMENTS_ROUTE = EXPERIMENT_ROUTE + "/assignments/"
ASSIGNMENT_ROUTE = ASSIGNMENTS_ROUTE + "<int:a_id>"


def get_participant_experiment_or_abort(experiment_id, code=400):
    """Return the ParticipantExperiment object corresponding to the current
    user and experiment_id or abort with the given code.
    """
    try:
        return ParticipantExperiment.query.\
            filter_by(participant_id=current_user.id).\
            filter_by(experiment_id=experiment_id).one()
    except NoResultFound:
        abort(code)


@experiments.route('/', methods=["GET"])
@login_required
def read_experiments():
    """List experiments.
    """
    now = datetime.now()
    past_experiments = Experiment.query.filter(Experiment.stop < now).all()
    present_experiments = Experiment.query.filter(Experiment.stop > now).\
        filter(Experiment.start < now).all()
    future_experiments = Experiment.query.filter(Experiment.start > now)

    create_form = CreateExperimentForm()

    return render_template("experiments/read_experiments.html",
                           past_experiments=past_experiments,
                           present_experiments=present_experiments,
                           future_experiments=future_experiments,
                           create_form=create_form)


@experiments.route("/", methods=["POST"])
@roles_required("experimenter")
def create_experiment():
    """Create an experiment and save it to the database.
    """
    form = CreateExperimentForm(request.form)
    if not form.validate():
        return jsonify({"success": 0, "errors": form.errors})

    exp = Experiment()
    form.populate_obj(exp)
    exp.created = datetime.now()
    exp.save()

    return jsonify({"success": 1})


@experiments.route(EXPERIMENT_ROUTE, methods=["GET"])
@login_required
def read_experiment(experiment_id):
    """View the landing page of an experiment, along with the ability to start.
    """
    exp = validate_model_id(Experiment, experiment_id)
    if current_user.has_role("participant"):
        part_exp = get_participant_experiment_or_abort(experiment_id)

        if len(part_exp.assignments) == 0:
            assignment = None
        else:
            assignment = part_exp.assignments[0]
    else:
        assignment = None

    return render_template("experiments/read_experiment.html", experiment=exp,
                           assignment=assignment)


@experiments.route(EXPERIMENT_ROUTE, methods=["DELETE"])
@roles_required("experimenter")
def delete_experiment(experiment_id):
    """Delete an experiment.
    """
    exp = validate_model_id(Experiment, experiment_id)

    db.session.delete(exp)
    db.session.commit()

    return jsonify({"success": 1, "next_url":
                    url_for('experiments.read_experiments')})


@experiments.route(EXPERIMENT_ROUTE, methods=["PUT"])
@roles_required("experimenter")
def update_experiment(experiment_id):
    """Modify an experiment's properties.
    """
    exp = validate_model_id(Experiment, experiment_id)

    experiment_update_form = CreateExperimentForm(request.form)

    if not experiment_update_form.validate():
        return jsonify({"success": 0, "errors": experiment_update_form.errors})

    experiment_update_form.populate_obj(exp)

    exp.save()

    return jsonify({"success": 1})


@experiments.route(ASSIGNMENT_ROUTE, methods=["GET"])
@roles_required("participant")
def read_assignment(experiment_id, a_id):
    """Given an assignment ID, retrieve it from the database and display it to
    the user.
    """
    experiment = validate_model_id(Experiment, experiment_id)
    assignment = validate_model_id(Assignment, a_id)

    part_exp = get_participant_experiment_or_abort(experiment_id)

    if assignment not in part_exp.assignments:
        abort(400)

    activity = validate_model_id(Activity, assignment.activity_id)

    if "question" in activity.type:
        return read_question(experiment, activity, assignment)

    abort(404)


def read_question(experiment, question, assignment):
    """Retrieve a question from the database and render its template.

    This function assumes that all necessary error checking has been done on
    its parameters.
    """

    question_form = get_question_form(question)
    question_form.populate_choices(question.choices)

    if assignment.choice_id:
        question_form.choices.default = str(assignment.choice_id)
        question_form.process()

    question_form.comment.data = assignment.comment

    part_exp = assignment.participant_experiment
    this_index = part_exp.assignments.index(assignment)

    if not part_exp.complete:
        # If the participant is not done, then save the choice order
        choice_order = [c.id for c in question.choices]
        assignment.choice_order = json.dumps(choice_order)
        assignment.save()
        next_url = None
        explanation = ""
    else:
        # If the participant is done, have a link right to the next question
        next_url = get_next_assignment_url(part_exp, this_index)
        explanation = question.explanation

    previous_assignment = None

    if this_index - 1 > -1:
        previous_assignment = part_exp.assignments[this_index - 1]

    return render_template("experiments/read_question.html", exp=experiment,
                           question=question, assignment=assignment,
                           mc_form=question_form,
                           next_url=next_url,
                           explanation=explanation,
                           experiment_complete=part_exp.complete,
                           previous_assignment=previous_assignment)


@experiments.route(ASSIGNMENT_ROUTE, methods=["PATCH"])
def update_assignment(experiment_id, a_id):
    """Record a user's answer to this assignment
    """
    assignment = validate_model_id(Assignment, a_id)
    validate_model_id(Experiment, experiment_id)
    part_exp = assignment.participant_experiment

    if part_exp.participant != current_user:
        abort(403)

    if part_exp.complete:
        abort(400)

    if "question" in assignment.activity.type:
        return update_question_assignment(part_exp, assignment)

    # Pass for now
    return jsonify({"success": 1})


def update_question_assignment(part_exp, assignment):
    """Update an assignment whose activity is a question.
    """
    question = assignment.activity

    question_form = get_question_form(question, request.form)
    question_form.populate_choices(question.choices)

    if not question_form.validate():
        return jsonify({"success": 0, "errors": question_form.errors})

    selected_choice = validate_model_id(Choice,
                                        int(question_form.choices.data), 400)

    # User has answered this question successfully
    this_index = part_exp.assignments.index(assignment)
    assignment.choice_id = selected_choice.id
    assignment.comment = question_form.comment.data

    if this_index == part_exp.progress:
        part_exp.progress += 1

    next_url = get_next_assignment_url(part_exp, this_index)

    db.session.commit()
    return jsonify({"success": 1, "next_url": next_url})


def get_next_assignment_url(participant_experiment, current_index):
    """Given an experiment, a participant_experiment, and the current index,
    find the url of the next assignment in the sequence.
    """
    experiment_id = participant_experiment.experiment.id
    try:
        # If there is a next assignment, return its url
        next_url = url_for(
            "experiments.read_assignment",
            experiment_id=experiment_id,
            a_id=participant_experiment.assignments[current_index + 1].id)
    except IndexError:
        next_url = None

    if not next_url:
        # We've reached the end of the experiment
        if not participant_experiment.complete:
            # The experiment needs to be submitted
            next_url = url_for("experiments.confirm_done_experiment",
                               experiment_id=experiment_id)
        else:
            # Experiment has already been submitted
            next_url = url_for("experiments.read_experiment",
                               experiment_id=experiment_id)

    return next_url


@experiments.route(EXPERIMENT_ROUTE + '/settings', methods=["GET"])
@roles_required("experimenter")
def settings_experiment(experiment_id):
    """Give information on an experiment and its activities.
    """
    experiment = validate_model_id(Experiment, experiment_id)

    update_experiment_form = CreateExperimentForm(obj=experiment)

    delete_experiment_form = DeleteObjectForm()

    import_assignment_form = ImportAssignmentForm()

    return render_template("experiments/settings_experiment.html",
                           experiment=experiment,
                           import_assignment_form=import_assignment_form,
                           update_experiment_form=update_experiment_form,
                           delete_experiment_form=delete_experiment_form)


@experiments.route(ASSIGNMENTS_ROUTE + 'import', methods=["POST"])
@roles_required("experimenter")
def import_assignments(experiment_id):
    """Given an uploaded spreadsheet, remove this experiment's assignments
    and replace them with the new, given assignments.
    """
    experiment = validate_model_id(Experiment, experiment_id)
    import_assignment_form = ImportAssignmentForm()

    if not import_assignment_form.validate():
        return jsonify({"success": 0, "errors": import_assignment_form.errors})

    workbook = openpyxl.load_workbook(import_assignment_form.assignments.data)

    # for part_exp in experiment.participant_experiments:
    #     db.session.delete(part_exp)
    # db.session.commit()

    import_export.import_data_from_workbook(workbook, experiment)

    return jsonify({"success": 1})


def get_question_stats(assignment, question_stats):
    """Given an assignment of a question and a stats array, return statistics
    about this question in the array.
    """
    question = assignment.activity
    if question.id not in question_stats:
        question_stats[question.id] = {
            "num_responses": 0,
            "num_correct": 0,
            "question_text": question.question,
        }

    if assignment.choice:
        question_stats[question.id]["num_responses"] += 1

        if assignment.choice.correct:
            question_stats[question.id]["num_correct"] += 1


@experiments.route(EXPERIMENT_ROUTE + "/results", methods=["GET"])
@roles_required("experimenter")
def results_experiment(experiment_id):
    """Render some results.
    """
    experiment = validate_model_id(Experiment, experiment_id)

    num_participants = Participant.query.count()
    num_finished = ParticipantExperiment.query.\
        filter_by(experiment_id=experiment.id).\
        filter_by(progress=-1).count()

    percent_finished = num_finished / float(num_participants)

    # {"question_id": {"question": "question_text", "num_responses":
    #   num_responses, "num_correct": num_correct], ...}
    question_stats = defaultdict(dict)

    for assignment in experiment.assignments:
        activity = assignment.activity

        if "question" in activity.type:
            get_question_stats(assignment, question_stats)

    return render_template("experiments/results_experiment.html",
                           experiment=experiment,
                           num_participants=num_participants,
                           num_finished=num_finished,
                           percent_finished=percent_finished,
                           question_stats=question_stats)


@experiments.route(EXPERIMENT_ROUTE + "/confirm_done", methods=["GET"])
@roles_required("participant")
def confirm_done_experiment(experiment_id):
    """Show the user a page before finalizing their quiz answers.
    """
    experiment = validate_model_id(Experiment, experiment_id)

    return render_template("experiments/confirm_done_experiment.html",
                           experiment=experiment)


@experiments.route(EXPERIMENT_ROUTE + "/finalize", methods=["PATCH"])
@roles_required("participant")
def finalize_experiment(experiment_id):
    """Finalize the user's answers for this experiment. They will no longer be
    able to edit them, but may view them.
    """
    validate_model_id(Experiment, experiment_id)
    part_exp = get_participant_experiment_or_abort(experiment_id)

    part_exp.complete = True

    db.session.commit()

    return jsonify({"success": 1,
                    "next_url": url_for('experiments.done_experiment',
                                        experiment_id=experiment_id)})


@experiments.route(EXPERIMENT_ROUTE + "/done", methods=["GET"])
@roles_required("participant")
def done_experiment(_):
    """Show the user a screen indicating that they are finished.
    """
    return render_template("experiments/done_experiment.html")


@experiments.app_template_filter("datetime_format")
def datetime_format_filter(value, fmt="%Y-%m-%d %H:%M:%S"):
    """Format the value (a datetime) according to fmt with strftime.
    """
    return value.strftime(fmt)


@experiments.app_template_filter("get_graph_url")
def get_graph_url_filter(graph):
    """Given a graph, return html to display it.
    """
    if os.path.isfile(graph.path):
        filename = graph.filename()
    else:
        filename = current_app.config.get("EXPERIMENTS_PLACEHOLDER_GRAPH")

    graph_path = url_for('static', filename=os.path.join("graphs", filename))
    return graph_path
