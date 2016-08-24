"""Forms for the Experiments blueprint.
"""

from datetime import datetime
import pdb

from flask_wtf import Form
from wtforms import SubmitField, RadioField, TextAreaField, HiddenField,\
    IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms_alchemy import ModelForm, ModelFormField

from quizApp.forms.common import OrderFormMixin, ScorecardSettingsForm
from quizApp.models import Experiment, MultipleChoiceQuestionResult, \
    IntegerQuestionResult, FreeAnswerQuestionResult, Choice


def get_question_form(question, data=None):
    """Given a question type, return the proper form that should be displayed
    to the participant.
    """
    form_mapping = {
        "question_mc_singleselect": MultipleChoiceForm,
        "question_mc_multiselect": MultipleChoiceForm,
        "question_freeanswer": FreeAnswerForm,
        "question_integer": IntegerAnswerForm,
        "question_mc_singleselect_scale": ScaleForm,
    }
    return form_mapping[question.type](data)


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

    def populate_from_question(self, question):
        """Given a question, perform any processing necessary to display the
        question - e.g. populate a list of choices, set field validators, etc.
        """
        raise NotImplementedError

    def populate_from_result(self, result):
        """Given a result, populate necessary defaults for this form.
        """
        raise NotImplementedError

    @property
    def result(self):
        """Generate a Result record based on this form.
        """
        raise NotImplementedError


class IntegerAnswerForm(QuestionForm):
    """Allow users to enter an integer as an answer.
    """
    integer = IntegerField()

    def populate_from_question(self, question):
        min_value = max_value = None
        if question.bounded_below:
            min_value = question.lower_bound
        if question.bounded_above:
            max_value = question.upper_bound
        self.integer.validators = [
            NumberRange(min_value, max_value)]


    def populate_from_result(self, result):
        self.integer.default = result.integer
        self.process()

    @property
    def result(self):
        return IntegerQuestionResult(integer=self.integer.data)


class FreeAnswerForm(QuestionForm):
    """Form for rendering a free answer Question.
    """
    text = TextAreaField()

    def populate_from_question(self, question):
        pass

    def populate_from_result(self, result):
        self.text.default = result.text
        self.process()

    @property
    def result(self):
        return FreeAnswerQuestionResult(text=self.text.data)


class MultipleChoiceForm(QuestionForm):
    """Form for rendering a multiple choice question with radio buttons.
    """
    choices = RadioField(validators=[DataRequired()], choices=[])

    def populate_from_question(self, question):
        """Given a pool of choices, populate the choices field.
        """
        self.choices.choices = [(str(c.id),
                                 "{} - {}".format(c.label, c.choice))
                                for c in question.choices]

    def populate_from_result(self, result):
        self.choices.default = str(result.choice_id)
        self.process()

    @property
    def result(self):
        return MultipleChoiceQuestionResult(
            choice=Choice.query.get(self.choices.data))


class ScaleForm(MultipleChoiceForm):
    """Form for rendering a likert scale question.
    """
    choices = LikertField(validators=[DataRequired()])

    def populate_from_question(self, question):
        self.choices.choices = [(str(c.id),
                                 "{}<br />{}".format(c.label, c.choice))
                                for c in question.choices]


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
