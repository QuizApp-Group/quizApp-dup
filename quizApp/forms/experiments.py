"""Forms for the Experiments blueprint.
"""
from datetime import datetime

from flask_wtf import Form
from wtforms import SubmitField, RadioField, TextAreaField, HiddenField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms_alchemy import ModelForm, ModelFormField

from quizApp.forms.common import OrderFormMixin, ScorecardSettingsForm, \
    MultiCheckboxField
from quizApp.models import Experiment, MultipleChoiceQuestionResult, \
    IntegerQuestionResult, FreeAnswerQuestionResult, Choice, \
    MultiSelectQuestionResult, ScorecardResult


def get_answer_form(activity, data=None):
    """Given an activity, return the proper form that should be displayed
    to the participant.
    """
    form_mapping = {
        "question_mc_singleselect": MultipleChoiceAnswerForm,
        "question_mc_multiselect": MultiSelectAnswerForm,
        "question_freeanswer": FreeAnswerForm,
        "question_integer": IntegerAnswerForm,
        "question_mc_singleselect_scale": ScaleAnswerForm,
        "scorecard": ScorecardAnswerForm,
    }
    return form_mapping[activity.type](data)


class LikertField(RadioField):
    """Field for displaying a Likert scale. The only difference from a
    RadioField is how its rendered, so this class is for rendering purposes.
    """
    pass


class ActivityAnswerForm(Form):
    """Form for rendering a general Activity. Mostly just for keeping track of
    render and submit time.
    """
    render_time = HiddenField()
    submit_time = HiddenField()
    submit = SubmitField("Submit")
    comment = TextAreaField()

    def populate_from_assignment(self, assignment):
        """Given an assignment, perform any processing necessary to display the
        activity - e.g. populate a list of choices, set field validators, etc.

        This will call ``populate_from_result`` as well as
        ``populate_from_activity``, so it will stomp on any form data in this
        form. This function is useful to call before rendering rather than
        before validation.
        """
        if assignment.result:
            self.populate_from_result(assignment.result)
        self.populate_from_activity(assignment.activity)
        self.comment.data = assignment.comment

    def populate_from_activity(self, activity):
        """Given an activity, populate defaults/validators/other things of that
        nature.

        This should not stomp on form data. This is called before validation to
        ensure that user input meets validation requirements.
        """
        raise NotImplementedError

    def populate_from_result(self, result):
        """Given a result object, populate this form as necessary.

        This will only be called if there is a result object associated with an
        assignment.
        """
        raise NotImplementedError

    def populate_assignment(self, assignment):
        """Populate the given assignment based on this form.
        """
        assignment.comment = self.comment.data
        result = self.result
        result.assignment = assignment

    @property
    def result(self):
        """Create a Result object based on this form's data.

        The Result should be appropriate to the type of activity this form is
        dealing with.
        """
        raise NotImplementedError


class ScorecardAnswerForm(ActivityAnswerForm):
    """Form to render when rendering a scorecard.
    """
    def populate_from_result(self, result):
        pass

    def populate_from_activity(self, activity):
        pass

    @property
    def result(self):
        return ScorecardResult()


class IntegerAnswerForm(ActivityAnswerForm):
    """Allow users to enter an integer as an answer.
    """
    integer = IntegerField()

    def populate_from_activity(self, activity):
        self.integer.validators = [NumberRange(activity.lower_bound,
                                               activity.upper_bound)]

    def populate_from_result(self, result):
        self.integer.default = result.integer
        self.process()

    @property
    def result(self):
        return IntegerQuestionResult(integer=self.integer.data)


class FreeAnswerForm(ActivityAnswerForm):
    """Form for rendering a free answer Question.
    """
    text = TextAreaField()

    def populate_from_activity(self, activity):
        pass

    def populate_from_result(self, result):
        self.text.default = result.text
        self.process()

    @property
    def result(self):
        return FreeAnswerQuestionResult(text=self.text.data)


class ChoiceAnswerFormMixin(object):
    """Multiselect and singleselect questions both populate their choices in
    the same way, so this class serves as a base class to handle this.
    """
    def populate_from_activity(self, question):
        """Given a pool of choices, populate the choices field.
        """
        choices = []
        for choice in question.choices:
            choices.append((str(choice.id), str(choice)))
        self.choices.choices = choices


class MultiSelectAnswerForm(ChoiceAnswerFormMixin, ActivityAnswerForm):
    """Form for rendering a multiple choice question with check boxes.
    """
    choices = MultiCheckboxField(validators=[DataRequired()], choices=[])

    def populate_from_result(self, result):
        self.choices.default = [str(c.id) for c in result.choices]
        self.process()

    @property
    def result(self):
        choices = [Choice.query.get(c) for c in self.choices.data]
        return MultiSelectQuestionResult(choices=choices)


class MultipleChoiceAnswerForm(ChoiceAnswerFormMixin, ActivityAnswerForm):
    """Form for rendering a multiple choice question with radio buttons.
    """
    choices = RadioField(validators=[DataRequired()], choices=[])

    def populate_from_result(self, result):
        self.choices.default = str(result.choice.id)
        self.process()

    @property
    def result(self):
        return MultipleChoiceQuestionResult(
            choice=Choice.query.get(self.choices.data))


class ScaleAnswerForm(MultipleChoiceAnswerForm):
    """Form for rendering a likert scale question.
    """
    choices = LikertField(validators=[DataRequired()])

    def populate_from_activity(self, activity):
        self.choices.choices = [(str(c.id),
                                 "{}<br />{}".format(c.label, c.choice))
                                for c in activity.choices]


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
