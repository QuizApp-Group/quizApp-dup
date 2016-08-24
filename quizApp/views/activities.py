"""Views for CRUD of activities.

In order to be as general as possible, each of the activity-specific views
tests the kind of activity it is loading and then defers to a more specific
function (for example, questions are read by read_question rather than
read_activity itself).
"""
from flask import Blueprint, render_template, url_for, jsonify, abort, request
from flask_security import roles_required

from quizApp.models import Activity, Dataset, Question, Choice
from quizApp.forms.experiments import get_question_form
from quizApp.forms.activities import DatasetListForm,\
    ChoiceForm, get_activity_form
from quizApp.forms.common import DeleteObjectForm, ObjectTypeForm
from quizApp import db
from quizApp.views.helpers import validate_model_id

activities = Blueprint("activities", __name__, url_prefix="/activities")

ACTIVITY_TYPES = {"question_mc_singleselect": "Single select multiple choice",
                  "question_mc_multiselect": "Multi select multiple choice",
                  "question_mc_singleselect_scale": "Likert scale",
                  "question_integer": "Integer answer",
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
    confirm_delete_activity_form = DeleteObjectForm()

    return render_template(
        "activities/read_activities.html",
        activities=activities_list,
        confirm_delete_activity_form=confirm_delete_activity_form,
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

    read_function_mapping = {
        "question_mc_singleselect": read_question,
        "question_mc_multiselect": read_question,
        "question_freeanswer": read_question,
        "question_integer": read_question,
        "question_mc_singleselect_scale": read_question,
    }
    return read_function_mapping[activity.type](activity)


def read_question(question):
    """Display a given question as it would appear to a participant.
    """
    form = get_question_form(question)

    form.populate_from_question(question)

    template_mapping = {
        "question_mc_singleselect": "activities/read_mc_question.html",
        "question_mc_multiselect": "activities/read_mc_question.html",
        "question_freeanswer": "activities/read_freeanswer_question.html",
        "question_integer": "activities/read_integer_question.html",
        "question_mc_singleselect_scale": "activities/read_mc_question.html",
    }

    return render_template(template_mapping[question.type],
                           question=question,
                           question_form=form)


@activities.route(ACTIVITY_ROUTE + "/settings", methods=["GET"])
@roles_required("experimenter")
def settings_activity(activity_id):
    """Display settings for a particular activity.
    """
    activity = validate_model_id(Activity, activity_id)

    settings_function_mapping = {
        "question_mc_singleselect": settings_question,
        "question_mc_multiselect": settings_question,
        "question_freeanswer": settings_question,
        "question_mc_singleselect_scale": settings_question,
        "question_integer": settings_question,
    }

    return settings_function_mapping[activity.type](activity)


def settings_question(question):
    """Return a settings page for a question.
    """
    general_form = get_activity_form(question, obj=question)

    dataset_form = DatasetListForm(prefix="dataset")
    dataset_form.reset_objects()
    dataset_form.populate_objects(Dataset.query.all())
    dataset_form.objects.default = [x.id for x in question.datasets]
    dataset_form.process()

    activity_type_form = ObjectTypeForm()
    activity_type_form.populate_object_type(ACTIVITY_TYPES)

    # These kwargs should be passed to all templates, regardless of the type of
    # question.
    template_kwargs = {
        "question": question,
        "general_form": general_form,
        "activity_type_form": activity_type_form,
        "dataset_form": dataset_form,
    }

    # If a question needs special forms on its settings page, it should extend
    # ``templates/activities/settings_question.html`` and add code as
    # necessary. Then it should be added here with a handler function, which
    # should render the template.
    settings_question_function_mapping = {
        "question_mc_singleselect": settings_mc_question,
        "question_mc_multiselect": settings_mc_question,
        "question_mc_singleselect_scale": settings_mc_question,
    }

    try:
        return settings_question_function_mapping[question.type](
            question, template_kwargs)
    except KeyError:
        pass

    return render_template(
        "activities/settings_question.html",
        **template_kwargs)


def settings_mc_question(question, template_kwargs):
    """Display settings for the given question.
    """
    template_kwargs["choices"] = question.choices
    template_kwargs["create_choice_form"] = ChoiceForm(prefix="create")
    template_kwargs["update_choice_form"] = ChoiceForm(prefix="update")
    template_kwargs["confirm_delete_choice_form"] = DeleteObjectForm()

    return render_template("activities/settings_mc_question.html",
                           **template_kwargs)


@activities.route(ACTIVITY_ROUTE, methods=["PUT"])
@roles_required("experimenter")
def update_activity(activity_id):
    """Update the activity based on transmitted form data.
    """
    activity = validate_model_id(Activity, activity_id)
    general_form = get_activity_form(activity, request.form, obj=activity)

    if not general_form.validate():
        return jsonify({"success": 0, "errors": general_form.errors})

    general_form.populate_obj(activity)
    db.session.commit()

    return jsonify({"success": 1})


@activities.route(ACTIVITY_ROUTE + "/datasets/<int:dataset_id>",
                  methods=["DELETE"])
@roles_required("experimenter")
def delete_question_dataset(activity_id, dataset_id):
    """Disassociate this question from a dataset.
    """
    activity = validate_model_id(Activity, activity_id)
    dataset = validate_model_id(Dataset, dataset_id)

    if dataset not in activity.datasets:
        abort(400)

    activity.datasets.remove(dataset)
    db.session.commit()

    return jsonify({"success": 1})


@activities.route(ACTIVITY_ROUTE + "/datasets/", methods=["POST"])
@roles_required("experimenter")
def create_question_dataset(activity_id):
    """Associate this question with a dataset.

    The request should contain the ID of the dataset to be associated.
    """
    activity = validate_model_id(Activity, activity_id)
    dataset_id = request.form["dataset_id"]
    dataset = validate_model_id(Dataset, dataset_id)

    if dataset in activity.datasets:
        abort(400)

    activity.datasets.append(dataset)
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

    return jsonify({
        "success": 1,
        "new_row": render_template("activities/render_choice_row.html",
                                   choice=choice)
    })


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
