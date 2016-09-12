"""Forms for the activities blueprint.
"""

from wtforms import SubmitField
from wtforms_alchemy import ModelForm, ModelFormField

from quizApp.forms.common import ListObjectForm, OrderFormMixin,\
    ScorecardSettingsForm
from quizApp.models import Choice, Question, Activity, \
    IntegerQuestion, Scorecard


class ActivityForm(OrderFormMixin, ModelForm):
    """Generalized class for creation/updating of Activities
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Activity
        order = ('question', '*', 'needs_comment', 'include_in_scorecards',
                 'scorecard_settings', 'submit')

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
        "scorecard": ActivityForm,
    }

    return activity_form_mapping[activity.type](*args, **kwargs)


class ScorecardForm(ActivityForm):
    """Form that can be used for creating or updating scorecards.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Scorecard


class QuestionForm(ActivityForm):
    """Form that can be used for creating or updating questions.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Question


class IntegerQuestionForm(ActivityForm):
    """Create or update an IntegerQuestion.
    """
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
