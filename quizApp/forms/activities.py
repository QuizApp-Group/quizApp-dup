"""Forms for the activities blueprint.
"""

from wtforms import SubmitField
from wtforms_alchemy import ModelForm

from quizApp.forms.common import ListObjectForm, OrderFormMixin
from quizApp.models import Choice, Question


class QuestionForm(OrderFormMixin, ModelForm):
    """Form that can be used for creating or updating questions.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Question
        order = ('*', 'submit')

    submit = SubmitField("Submit")


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

    submit = SubmitField("Submit")
