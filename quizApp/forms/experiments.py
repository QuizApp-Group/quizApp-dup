"""Forms for the Experiments blueprint.
"""

from datetime import datetime

from flask_wtf import Form
from wtforms import SubmitField, RadioField, TextAreaField, HiddenField
from wtforms.validators import DataRequired
from wtforms_alchemy import ModelForm, ModelFormField

from quizApp.forms.common import OrderFormMixin, ScorecardSettingsForm
from quizApp.models import Experiment


def get_question_form(question, data=None):
    """Given a question type, return the proper form.
    """
    if "scale" in question.type:
        return ScaleForm(data)
    else:
        return MultipleChoiceForm(data)


class LikertField(RadioField):
    """Field for displaying a Likert scale. The only difference from a
    RadioField is how its rendered, so this class is for rendering purposes.
    """
    pass


class ActivityForm(Form):
    """Form for rendering a general Activity. Mostly just for keeping track of
    render and submit time.
    """
    render_time = HiddenField()
    submit_time = HiddenField()


class QuestionForm(ActivityForm):
    """Form for rendering a general Question.
    """
    submit = SubmitField("Submit")
    comment = TextAreaField()

    def populate_choices(self, choice_pool):
        """Child classes should implement this themselves for choice selection.
        """
        pass


class MultipleChoiceForm(QuestionForm):
    """Form for rendering a multiple choice question with radio buttons.
    """
    choices = RadioField(validators=[DataRequired()], choices=[])

    def populate_choices(self, choice_pool):
        """Given a pool of choices, populate the choices field.
        """
        self.choices.choices = [(str(c.id),
                                 "{} - {}".format(c.label, c.choice))
                                for c in choice_pool]


class ScaleForm(QuestionForm):
    """Form for rendering a likert scale question.
    """
    choices = LikertField(validators=[DataRequired()])

    def populate_choices(self, choice_pool):
        """Given a pool of choices, populate the choices field.
        """
        self.choices.choices = [(str(c.id),
                                 "{}<br />{}".format(c.label, c.choice))
                                for c in choice_pool]


class CreateExperimentForm(OrderFormMixin, ModelForm):
    """Form for creating or updating an experiment's properties.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Experiment
        exclude = ['created']
        order = ('*', 'scorecard_settings', 'submit')

    scorecard_settings = ModelFormField(ScorecardSettingsForm)
    submit = SubmitField("Save")

    def validate(self):
        """Validate the start and stop times, then do the rest as usual.
        """
        if not super(CreateExperimentForm, self).validate():
            return False

        valid = True
        if self.start.data >= self.stop.data:
            self.start.errors.append("Start time must be before stop time.")
            valid = False

        if self.stop.data < datetime.now():
            self.stop.errors.append("Stop time may not be in past")
            valid = False

        return valid
