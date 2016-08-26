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
from quizApp.views.common import ObjectCollectionView

activities = Blueprint("activities", __name__, url_prefix="/activities")

ACTIVITY_TYPES = {"question_mc_singleselect": "Single select multiple choice",
                  "question_mc_multiselect": "Multi select multiple choice",
                  "question_mc_singleselect_scale": "Likert scale",
                  "question_integer": "Integer answer",
                  "question_freeanswer": "Free answer"}

ACTIVITY_ROUTE = "/<int:activity_id>"
CHOICES_ROUTE = "/<int:question_id>/choices/"
CHOICE_ROUTE = CHOICES_ROUTE + "<int:choice_id>"


class ActivityCollectionView(ObjectCollectionView):
    """View for the activity collection.
    """
    decorators = [roles_required("experimenter")]
    methods = ["GET", "POST"]
    resolve_kwargs = dict
    template = "activities/read_activities.html"

    def get_members(self):
        return Activity.query.all()

    def create_form(self):
        activity_type_form = ObjectTypeForm()
        activity_type_form.populate_object_type(ACTIVITY_TYPES)
        return activity_type_form

    def create_member(self, create_form):
        activity = Activity(type=create_form.object_type.data)
        activity.save()
        return {"next_url": url_for("activities.read_activity",
                                    activity_id=activity.id)}

activities.add_url_rule("/",
                        view_func=ActivityCollectionView.as_view('activities'))


def render_activity(activity, *args, **kwargs):
    """Given an activity, render the template that displays this activity and
    return it.

    This function is the central place where activities are rendered.

    Extra args/kwargs will be passed on to the specific rendering function for
    the type of activity.
    """

    render_mapping = {
        "question_mc_singleselect": render_question,
        "question_mc_multiselect": render_question,
        "question_freeanswer": render_question,
        "question_integer": render_question,
        "question_mc_singleselect_scale": render_question,
    }

    return render_mapping[activity.type](activity, *args, **kwargs)


@activities.route(ACTIVITY_ROUTE, methods=["GET"])
@roles_required("experimenter")
def read_activity(activity_id):
    """Display a given activity as it would appear to a participant.
    """
    activity = validate_model_id(Activity, activity_id)
    rendered_activity = render_activity(activity, False)

    return render_template("activities/read_activity.html",
                           activity=activity,
                           rendered_activity=rendered_activity)


def render_question(question, disabled=False, assignment=None,
                    render_explanation=True):
    """Display a given question as it would appear to a participant.

    Arguments:
        question (Question): The question to render
        disabled (bool): if True, disable the form controls
        assignment (Assignment): if given, use the assignment's result and
            comment to populate fields prior to rendering
        render_explanation (bool): If True, render the explanation for this
            question
    """
    form = get_question_form(question)
    form.populate_from_question(question)

    try:
        form.populate_from_result(assignment.result)
    except AttributeError:
        pass

    try:
        form.comment.default = assignment.comment
        form.process()
    except AttributeError:
        pass

    template_mapping = {
        "question_mc_singleselect": "activities/render_mc_question.html",
        "question_mc_multiselect": "activities/render_mc_question.html",
        "question_freeanswer": "activities/render_freeanswer_question.html",
        "question_integer": "activities/render_integer_question.html",
        "question_mc_singleselect_scale": "activities/render_mc_question.html",
    }

    return render_template(template_mapping[question.type],
                           question=question, form=form, disabled=disabled,
                           render_explanation=render_explanation)


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

    next_url = url_for("activities.activities")

    return jsonify({"success": 1, "next_url": next_url})


class ChoiceCollectionView(ObjectCollectionView):
    """Handle a collection of choices.
    """
    decorators = [roles_required("experimenter")]
    methods = ["POST"]
    get_members = None

    def resolve_kwargs(self, question_id):
        question = validate_model_id(Question, question_id)
        return {"question": question}

    def create_form(self):
        return ChoiceForm(request.form, prefix="create")

    template = None

    def create_member(self, create_form, question):
        choice = Choice()

        create_form.populate_obj(choice)
        question.choices.append(choice)

        choice.save()
        db.session.commit()

        return {"new_row": render_template("activities/render_choice_row.html",
                                           choice=choice)}

activities.add_url_rule(CHOICES_ROUTE,
                        view_func=ChoiceCollectionView.as_view('choices'))


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
