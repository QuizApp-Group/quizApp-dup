"""Views for CRUD of activities.

In order to be as general as possible, each of the activity-specific views
tests the kind of activity it is loading and then defers to a more specific
function (for example, questions are read by read_question rather than
read_activity itself).
"""
from flask import Blueprint, render_template, url_for, jsonify, abort, request
from flask_security import roles_required
from sqlalchemy import not_

from quizApp.models import Activity, Dataset, Question, Choice
from quizApp.forms.experiments import get_question_form
from quizApp.forms.activities import QuestionForm, DatasetListForm,\
    ChoiceForm
from quizApp.forms.common import DeleteObjectForm, ObjectTypeForm
from quizApp import db
from quizApp.views.helpers import validate_model_id

activities = Blueprint("activities", __name__, url_prefix="/activities")

ACTIVITY_TYPES = {"question_mc_singleselect": "Single select multiple choice",
                  "question_mc_multiselect": "Multi select multiple choice",
                  "question_mc_singleselect_scale": "Likert scale",
                  "question_freeanswer": "Free answer"}

ACTIVITY_ROUTE = "/<int:activity_id>"
CHOICES_ROUTE = "/<int:question_id>/choices/"
CHOICE_ROUTE = CHOICES_ROUTE + "<int:choice_id>"


@activities.route('/', methods=["GET"])
@roles_required("experimenter")
def read_activities():
    """Display a list of all activities.
    """
    activities_list = Activity.query.all()
    activity_type_form = ObjectTypeForm()
    activity_type_form.populate_object_type(ACTIVITY_TYPES)

    return render_template("activities/read_activities.html",
                           activities=activities_list,
                           activity_type_form=activity_type_form)


@activities.route("/", methods=["POST"])
@roles_required("experimenter")
def create_activity():
    """Create an activity.
    """
    activity_type_form = ObjectTypeForm()
    activity_type_form.populate_object_type(ACTIVITY_TYPES)

    if not activity_type_form.validate():
        return jsonify({"success": 0, "errors": activity_type_form.errors})

    activity = Activity(type=activity_type_form.object_type.data)
    activity.save()

    next_url = url_for("activities.settings_activity", activity_id=activity.id)

    return jsonify({"success": 1, "next_url": next_url})


@activities.route(ACTIVITY_ROUTE, methods=["GET"])
@roles_required("experimenter")
def read_activity(activity_id):
    """Display a given activity as it would appear to a participant.
    """
    activity = validate_model_id(Activity, activity_id)

    if "question" in activity.type:
        return read_question(activity)


def read_question(question):
    """Display a given question as it would appear to a participant.
    """
    form = get_question_form(question)

    form.populate_choices(question.choices)

    return render_template("activities/read_question.html",
                           question=question,
                           question_form=form)


@activities.route(ACTIVITY_ROUTE + "/settings", methods=["GET"])
@roles_required("experimenter")
def settings_activity(activity_id):
    """Display settings for a particular activity.
    """
    activity = validate_model_id(Activity, activity_id)

    if "question" in activity.type:
        return settings_question(activity)


def settings_question(question):
    """Display settings for the given question.
    """
    general_form = QuestionForm(obj=question)

    dataset_form = DatasetListForm()
    dataset_form.reset_objects()
    remove_dataset_mapping = dataset_form.populate_objects(question.datasets)
    add_dataset_mapping = dataset_form.populate_objects(
        Dataset.query.
        filter(not_(Dataset.questions.any(id=question.id))).all())

    if "mc" in question.type:
        create_choice_form = ChoiceForm(prefix="create")
        update_choice_form = ChoiceForm(prefix="update")
    else:
        create_choice_form = None
        update_choice_form = None

    delete_activity_form = DeleteObjectForm(prefix="activity")
    delete_choice_form = DeleteObjectForm(prefix="choice")

    return render_template("activities/settings_question.html",
                           question=question,
                           general_form=general_form,
                           dataset_form=dataset_form,
                           remove_dataset_mapping=remove_dataset_mapping,
                           add_dataset_mapping=add_dataset_mapping,
                           choices=question.choices,
                           create_choice_form=create_choice_form,
                           delete_activity_form=delete_activity_form,
                           delete_choice_form=delete_choice_form,
                           update_choice_form=update_choice_form)


@activities.route(ACTIVITY_ROUTE, methods=["PUT"])
@roles_required("experimenter")
def update_activity(activity_id):
    """Update the activity based on transmitted form data.
    """
    activity = validate_model_id(Activity, activity_id)

    if "question" in activity.type:
        return update_question(activity)


def update_question(question):
    """Given a question, update its settings.
    """
    general_form = QuestionForm(request.form)

    if not general_form.validate():
        return jsonify({"success": 0, "errors": general_form.errors})

    general_form.populate_obj(question)

    return jsonify({"success": 1})


@activities.route(ACTIVITY_ROUTE + "/datasets", methods=["PATCH"])
@roles_required("experimenter")
def update_question_datasets(activity_id):
    """Change the datasets that this question is associated with.
    """
    question = validate_model_id(Question, activity_id)
    dataset_form = DatasetListForm(request.form)
    dataset_mapping = dataset_form.populate_objects(Dataset.query.all())
    if not dataset_form.validate():
        return jsonify({"success": 0, "errors": dataset_form.errors})

    for dataset_id in dataset_form.objects.data:
        dataset = dataset_mapping[dataset_id]

        if dataset in question.datasets:
            question.datasets.remove(dataset)
        else:
            question.datasets.append(dataset)

    db.session.commit()

    return jsonify({"success": 1})


@activities.route(ACTIVITY_ROUTE, methods=["DELETE"])
@roles_required("experimenter")
def delete_activity(activity_id):
    """Delete the given activity.
    """
    activity = validate_model_id(Activity, activity_id)

    db.session.delete(activity)
    db.session.commit()

    next_url = url_for("activities.read_activities")

    return jsonify({"success": 1, "next_url": next_url})


@activities.route(CHOICES_ROUTE, methods=["POST"])
@roles_required("experimenter")
def create_choice(question_id):
    """Create a choice for the given question.
    """
    question = validate_model_id(Question, question_id)

    create_choice_form = ChoiceForm(request.form, prefix="create")

    if not create_choice_form.validate():
        return jsonify({"success": 0, "prefix": "create-",
                        "errors": create_choice_form.errors})

    choice = Choice()

    create_choice_form.populate_obj(choice)
    question.choices.append(choice)

    choice.save()
    db.session.commit()

    return jsonify({"success": 1})


@activities.route(CHOICE_ROUTE, methods=["PUT"])
@roles_required("experimenter")
def update_choice(question_id, choice_id):
    """Update the given choice using form data.
    """
    question = validate_model_id(Question, question_id)
    choice = validate_model_id(Choice, choice_id)

    if choice not in question.choices:
        abort(404)

    update_choice_form = ChoiceForm(request.form, prefix="update")

    if not update_choice_form.validate():
        return jsonify({"success": 0, "prefix": "update-",
                        "errors": update_choice_form.errors})

    update_choice_form.populate_obj(choice)

    db.session.commit()

    return jsonify({"success": 1})


@activities.route(CHOICE_ROUTE, methods=["DELETE"])
@roles_required("experimenter")
def delete_choice(question_id, choice_id):
    """Delete the given choice.
    """
    question = validate_model_id(Question, question_id)
    choice = validate_model_id(Choice, choice_id)

    if choice not in question.choices:
        abort(404)

    db.session.delete(choice)
    db.session.commit()

    return jsonify({"success": 1})
