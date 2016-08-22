"""Views for CRUD of activities.

In order to be as general as possible, each of the activity-specific views
tests the kind of activity it is loading and then defers to a more specific
function (for example, questions are read by read_question rather than
read_activity itself).
"""
from flask import Blueprint, render_template, url_for, jsonify, abort, \
    request
from flask_security import roles_required
from sqlalchemy import not_

from quizApp.models import Activity, Dataset, Question, Choice
from quizApp.forms.experiments import get_question_form
from quizApp.forms.activities import QuestionForm, DatasetListForm,\
    ChoiceForm
from quizApp.forms.common import DeleteObjectForm, ObjectTypeForm
from quizApp import db
from quizApp.views.helpers import validate_model_id
from quizApp.views.common import ObjectListView, ObjectView

activities = Blueprint("activities", __name__, url_prefix="/activities")

ACTIVITY_TYPES = {"question_mc_singleselect": "Single select multiple choice",
                  "question_mc_multiselect": "Multi select multiple choice",
                  "question_mc_singleselect_scale": "Likert scale",
                  "question_freeanswer": "Free answer"}

ACTIVITY_ROUTE = "/<int:activity_id>"
CHOICES_ROUTE = "/<int:question_id>/choices/"
CHOICE_ROUTE = CHOICES_ROUTE + "<int:choice_id>"


class ActivityListView(ObjectListView):
    """Views for the Activity collection.
    """
    decorators = [roles_required("experimenter")]
    read_template = "activities/read_activities.html"
    model = Activity

    def create_form(self, *_, **__):
        """Return a create form, which needs to be populated in this case.
        """
        activity_type_form = ObjectTypeForm()
        activity_type_form.populate_object_type(ACTIVITY_TYPES)
        return activity_type_form

    def member_url(self, record):
        return url_for("activities.settings_activity",
                       activity_id=record.id)

activities.add_url_rule('/', view_func=ActivityListView.as_view("activities"))


def read_question(question):
    """Display a given question as it would appear to a participant.
    """
    form = get_question_form(question)

    form.populate_choices(question.choices)

    return render_template("activities/read_question.html",
                           question=question,
                           question_form=form)


class ActivityView(ObjectView):
    """Views for a specific Activity.
    """
    decorators = [roles_required("experimenter")]

    def update_form(self, record, data):
        update_form_mapping = {
            "question_mc_singleselect": QuestionForm,
            "question_mc_multiselect": QuestionForm,
            "question_mc_singleselect_scale": QuestionForm,
            "question_freeanswer": QuestionForm
        }

        return update_form_mapping[record.type](data)

    def get_record(self, activity_id):
        return validate_model_id(Activity, activity_id)

    def collection_url(self, **_):
        return url_for("activities.activities")

    get_mapping = {
        "question_mc_singleselect": read_question,
        "question_mc_multiselect": read_question,
        "question_mc_singleselect_scale": read_question,
        "question_freeanswer": read_question
    }

activities.add_url_rule(ACTIVITY_ROUTE,
                        view_func=ActivityView.as_view("activity"))


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


class ChoiceView(ObjectView):
    """Views for a specific Choice object.
    """
    def update_form(self, record, form):
        return ChoiceForm(request.form, prefix="update")

    def get_record(self, question_id, choice_id):
        question = validate_model_id(Question, question_id)
        choice = validate_model_id(Choice, choice_id)

        if choice.question != question:
            abort(404)

        return choice

    def collection_url(self, question_id, **kwargs):
        return url_for("activities.settings_activity", activity_id=question_id)

activities.add_url_rule(CHOICE_ROUTE,
                        view_func=ChoiceView.as_view("choice"))
