"""Forms for the activities blueprint.
"""

from wtforms import SubmitField
from wtforms_alchemy import ModelForm, ModelFormField

from quizApp.forms.common import ListObjectForm, OrderFormMixin,\
    ScorecardSettingsForm
from quizApp.models import Choice, Question, Activity


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


class QuestionForm(ActivityForm):
    """Form that can be used for creating or updating questions.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Question


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
