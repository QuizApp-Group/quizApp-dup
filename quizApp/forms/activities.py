"""Forms for the activities blueprint.
"""

from wtforms import SubmitField
from wtforms_alchemy import ModelForm, ModelFormField

from quizApp.forms.common import ListObjectForm, OrderFormMixin,\
    ScorecardSettingsForm
from quizApp.models import Choice, Question, Activity, FreeAnswerQuestion,\
    IntegerQuestion


class ActivityForm(OrderFormMixin, ModelForm):
    """Generalized class for creation/updating of Activities
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Activity
        order = ('*', 'scorecard_settings', 'submit')

    scorecard_settings = ModelFormField(ScorecardSettingsForm)
    submit = SubmitField("Save")

def get_activity_form(activity, *args, **kwargs):
    """Return the update form for the actiivty of the given type.
    """
    activity_form_mapping = {
        "question_mc_singleselect": QuestionForm,
        "question_mc_multiselect": QuestionForm,
        "question_freeanswer": QuestionForm,
        "question_mc_singleselect_scale": QuestionForm,
        "question_integer": IntegerQuestionForm,
    }

    return activity_form_mapping[activity.type](*args, **kwargs)

class QuestionForm(ActivityForm):
    """Form that can be used for creating or updating questions.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Question

class IntegerQuestionForm(ActivityForm):
    class Meta(object):
        """Specify model and field order.
        """
        model = IntegerQuestion


class DatasetListForm(ListObjectForm):
    """List a bunch of datasets.
    """

    def get_choice_tuple(self, dataset):
        self.objects.choices.append((str(dataset.id), dataset.name))


class ChoiceForm(OrderFormMixin, ModelForm):
    """Form for creating or updating choices.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Choice
        order = ('*', 'submit')

    submit = SubmitField("Save")
