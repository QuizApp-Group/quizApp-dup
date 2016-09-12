"""Models for the quizApp.
"""
from __future__ import unicode_literals
from builtins import object
import os
from datetime import datetime

from quizApp import db
from flask_security import UserMixin, RoleMixin


class Base(db.Model):
    """Base class for all models.

    All models have an identical id field.

    Attributes:
        id (int): A unique identifier.
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    def save(self, commit=True):
        """Save this model to the database.

        If commit is True, then the session will be comitted as well.
        """
        db.session.add(self)

        if commit:
            db.session.commit()

    def import_dict(self, **kwargs):
        """Populate this object using data imported from a spreadsheet or
        similar. This means that not all fields will be passed into this
        function, however there are enough fields to populate all necessary
        fields. Due to validators, some fields need to be populated before
        others. Subclasses of Base to which this applies are expected to
        override this method and implement their import correctly.
        """
        for key, value in list(kwargs.items()):
            setattr(self, key, value)


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(),
                                 db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(),
                                 db.ForeignKey('role.id')))


class Role(Base, RoleMixin):
    """A Role describes what a User can and can't do.
    """
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(Base, UserMixin):
    """A User is used for authentication.

    Attributes:
        name (string): The username of this user.
        password (string): This user's password.
        authenticated (bool): True if this user is authenticated.
        type (string): The type of this user, e.g. experimenter, participant
    """

    email = db.Column(db.String(255), unique=True)
    active = db.Column(db.Boolean())
    password = db.Column(db.String(255), nullable=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship("Role", secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    type = db.Column(db.String(50), nullable=False)

    def has_any_role(self, roles):
        """Given a list of Roles, return True if the user has at least one of
        them.
        """
        return any(self.has_role(role) for role in roles)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }


participant_dataset_table = db.Table(
    "participant_dataset", db.metadata,
    db.Column('participant_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id'))
)


class Participant(User):
    """A User that takes Experiments.

    Attributes:
        opt_in (bool): Has this user opted in to data collection?
        foreign_id (str): If the user is coming from an external source (e.g.
            canvas, mechanical turk) it may be necessary to record their user
            ID on the other service (e.g. preventing multiple submission). This
            field holds the foreign ID of this user.
        assignments (list of Assignments): List of assignments that this user
            has
        assignment_sets (list of AssignmentSets): List of
            AssignmentSets that this participant has
    """

    opt_in = db.Column(db.Boolean)
    foreign_id = db.Column(db.String(100))

    assignments = db.relationship("Assignment", back_populates="participant")
    experiments = db.relationship("AssignmentSet",
                                  back_populates="participant")

    __mapper_args__ = {
        'polymorphic_identity': 'participant',
    }


class AssignmentSet(Base):
    """An Association Object that relates a User to an Experiment and also
    stores the progress of the User in this Experiment as well as the order of
    Questions that this user does.
    Essentially, this tracks the progress of each User in each Experiment.

    Attributes:
        activities (list of Activity): Order of activities for this
            user in this experiment
        progress (int): Which question the user is currently working on.
        complete (bool): True if the user has finalized their responses, False
            otherwise
        participant (Participant): Which Participant this refers to
        experiment (Experiment): Which Experiment this refers to
        assignments (list of Assignment): The assignments that this Participant
            should do in this Experiment
    """
    class Meta(object):
        """Specify field order.
        """
        field_order = ('*', 'assignments')

    progress = db.Column(db.Integer, nullable=False, default=0,
                         info={"import_include": False})
    complete = db.Column(db.Boolean, default=False,
                         info={"import_include": False})

    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    participant = db.relationship("Participant", back_populates="experiments",
                                  info={"import_include": False})

    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    experiment = db.relationship("Experiment",
                                 back_populates="assignment_sets")

    assignments = db.relationship("Assignment",
                                  back_populates="assignment_set")

    @property
    def score(self):
        """Return the cumulative score of all assignments in this
        AssignmentSet,

        Currently this iterates through all assignments. Profiling will be
        required to see if this is too slow.
        """
        score = 0

        for assignment in self.assignments[:self.progress]:
            score += assignment.score

        return score

    @db.validates('assignments')
    def validate_assignments(self, _, assignment):
        """The Assignments in this model must be related to the same Experiment
        as this model is."""
        assert assignment.participant == self.participant
        return assignment

    def import_dict(self, **kwargs):
        experiment = kwargs.pop("experiment")
        self.experiment = experiment

        super(AssignmentSet, self).import_dict(**kwargs)

assignment_media_item_table = db.Table(
    "assignment_media_item", db.metadata,
    db.Column("assignment_id", db.Integer,
              db.ForeignKey("assignment.id")),
    db.Column("media_item_id", db.Integer, db.ForeignKey("media_item.id"))
)


class Assignment(Base):
    """For a given Activity, determine which MediaItems, if any, a particular
    Participant sees, as well as recording the Participant's answer, or if
    they skipped this assignment.

    Attributes:
        skipped (bool): True if the Participant skipped this Question, False
             otherwise
        comment (string): An optional comment entered by the student.
        choice_order (string): A JSON object in string form that represents the
            order of choices that this participant was presented with when
            answering this question, e.g. {[1, 50, 9, 3]} where the numbers are
            the IDs of those choices.
        time_to_submit (timedelta): Time from the question being rendered to
            the question being submitted.
        media_items (list of MediaItem): What MediaItems should be shown
        participant (Participant): Which Participant gets this Assignment
        activity (Activity): Which Activity this Participant should see
        choice (Choice): Which Choice this Participant chose as their answer
        assignment_set (AssignmentSet): Which
            AssignmentSet this Assignment belongs to
    """

    skipped = db.Column(db.Boolean, info={"import_include": False})
    comment = db.Column(db.String(500), info={"import_include": False})
    choice_order = db.Column(db.String(80), info={"import_include": False})
    time_to_submit = db.Column(db.Interval(), info={"import_include": False})

    media_items = db.relationship("MediaItem",
                                  secondary=assignment_media_item_table,
                                  back_populates="assignments")

    participant_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    participant = db.relationship("Participant", back_populates="assignments",
                                  info={"import_include": False})

    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"))
    activity = db.relationship("Activity", back_populates="assignments")

    result_id = db.Column(db.Integer, db.ForeignKey("result.id"))
    result = db.relationship("Result", back_populates="assignment",
                             info={"import_include": False}, uselist=False)

    assignment_set_id = db.Column(
        db.Integer,
        db.ForeignKey("assignment_set.id"),
    )
    assignment_set = db.relationship("AssignmentSet",
                                     info={"import_include": False},
                                     back_populates="assignments")

    @property
    def correct(self):
        """Check if this assignment was answered correctly.
        """
        return self.activity.is_correct(self.result)

    @property
    def score(self):
        """Get the score for this assignment.

        This method simply passes `result` to the `activity`'s `get_score`
        method and returns the result.

        Note that if there is no `activity` this will raise an AttributeError.
        """
        return self.activity.get_score(self.result)

    @db.validates("activity")
    def validate_activity(self, _, activity):
        """Make sure that the activity is part of this experiment.
        Make sure that the number of media items on the activity is the same as
        the number of media items this assignment has.
        """
        try:
            assert (activity.num_media_items == len(self.media_items)) or \
                activity.num_media_items == -1
        except AttributeError:
            pass

        return activity

    @db.validates("result")
    def validate_result(self, _, result):
        """Make sure that this assignment has the correct type of result.
        """
        assert isinstance(result, self.activity.Meta.result_class)
        return result


class Result(Base):
    """A Result is the outcome of a Participant completing an Activity.

    Different Activities have different data that they generate, so this model
    does not actually contain any information on the outcome of an Activity.
    That is something that child classes of this class must define in their
    schemas.

    On the Assignment level, the type of Activity will determine the type of
    Result.

    Attributes:
        assignment (Assignment): The Assignment that owns this Result.
    """

    assignment = db.relationship("Assignment", back_populates="result",
                                 uselist=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        "polymorphic_identity": "result",
        "polymorphic_on": type,
    }


class IntegerQuestionResult(Result):
    """The integer entered as an answer to an Integer Question.

    Attributes:
        integer (int): The answer entered to this question.
    """
    integer = db.Column(db.Integer)

    __mapper_args__ = {
        "polymorphic_identity": "integer_question_result",
    }


class MultipleChoiceQuestionResult(Result):
    """The Choice that a Participant picked in a MultipleChoiceQuestion.
    """
    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
    choice = db.relationship("Choice")

    @db.event.listens_for(Result.assignment, "set", propagate=True)
    def validate_choice(self, value, *_):
        """Make sure this Choice is a valid option for this Question.
        """
        # This is kind of ugly, but the fact is that sqlalchemy does not have a
        # good way of validating an attribute of a parent. See this issue for
        # more details:
        # bitbucket.org/zzzeek/sqlalchemy/issues/2943/
        # To work around this, we check if the class we are currently operating
        # on is in fact a MultipleChoiceQuestionResult.
        if self.type == "mc_question_result":
            assert self.choice in value.activity.choices

    __mapper_args__ = {
        "polymorphic_identity": "mc_question_result",
    }


result_choice_table = db.Table(
    'result_choice', db.metadata,
    db.Column("choice_id", db.Integer, db.ForeignKey('choice.id')),
    db.Column("result_id", db.Integer, db.ForeignKey('result.id')),
)


class MultiSelectQuestionResult(Result):
    """The Choices that a Participant picked in a MultiSelectQuestion.
    """
    choices = db.relationship("Choice", secondary=result_choice_table)

    @db.event.listens_for(Result.assignment, "set", propagate=True)
    def validate_choice(self, value, *_):
        """Make sure this Choice is a valid option for this Question.
        """
        if self.type == "multiselect_question_result":
            for choice in self.choices:
                assert choice in value.activity.choices

    __mapper_args__ = {
        "polymorphic_identity": "multiselect_question_result",
    }


class FreeAnswerQuestionResult(Result):
    """What a Participant entered into a text box.
    """
    text = db.Column(db.String(500))

    __mapper_args__ = {
        "polymorphic_identity": "free_answer_question_result",
    }


class Activity(Base):
    """An Activity is essentially a screen that a User sees while doing an
    Experiment. It may be an instructional screen or show a Question, or do
    something else.

    This class allows us to use Inheritance to easily have a variety of
    Activities in an Experiment, since we have a M2M between Experiment
    and Activity, while a specific Activity may actually be a Question thanks
    to SQLAlchemy's support for polymorphism.

    Attributes:
        type (string): Discriminator column that determines what kind
            of Activity this is.
        needs_comment (bool): True if the participant should be asked why
            they picked what they did after they answer the question.
        category (string): A description of this assignment's category, for the
            users' convenience.
        experiments (list of Experiment): What Experiments include this
            Activity
        assignments (list of Assignment): What Assignments include this
            Activity
        scorecard_settings (ScorecardSettings): Settings for scorecards after
            this Activity is done
    """
    class Meta(object):
        """Define what kind of Result we are looking for.
        """
        result_class = Result

    type = db.Column(db.String(50), nullable=False)
    needs_comment = db.Column(db.Boolean(), info={"label": "Allow comments"})
    include_in_scorecards = db.Column(
        db.Boolean(), default=True,
        info={"label": "Include this activity in any aggregate scorecards"})

    assignments = db.relationship("Assignment", back_populates="activity",
                                  cascade="all")
    category = db.Column(db.String(100), info={"label": "Category"})

    scorecard_settings_id = db.Column(db.Integer,
                                      db.ForeignKey("scorecard_settings.id"))
    scorecard_settings = db.relationship("ScorecardSettings",
                                         info={"import_include": False})

    def __init__(self, *args, **kwargs):
        """Make sure to populate scorecard_settings.
        """
        self.scorecard_settings = ScorecardSettings()
        super(Activity, self).__init__(*args, **kwargs)

    def get_score(self, result):
        """Get the participant's score for this Activity.

        Given a Result object, an Activity subclass should be able to
        "score" the result in some way, and return an integer quantifying the
        Participant's performance.
        """
        pass

    def is_correct(self, result):
        """Given a result, return True if the answer was correct or False
        otherwise.

        If this activity does not have a concept of correct/incorrect, return
        None.
        """
        pass

    def import_dict(self, **kwargs):
        """If we are setting assignments, we need to update experiments to
        match.
        """
        assignments = kwargs.pop("assignments")
        for assignment in assignments:
            self.assignments.append(assignment)

        super(Activity, self).import_dict(**kwargs)

    __mapper_args__ = {
        'polymorphic_identity': 'activity',
        'polymorphic_on': type
    }

question_dataset_table = db.Table(
    "question_dataset", db.metadata,
    db.Column("question_id", db.Integer, db.ForeignKey("activity.id")),
    db.Column("dataset_id", db.Integer, db.ForeignKey("dataset.id"))
)


class Scorecard(Activity):
    """A Scorecard shows some kind of information about all previous
    activities.
    """
    def get_score(self, result):
        return 0

    def is_correct(self, result):
        return True

    __mapper_args__ = {
        'polymorphic_identity': 'scorecard',
    }


class Question(Activity):
    """A Question is related to one or more MediaItems and has one or more Choices,
    and is a part of one or more Experiments.

    Attributes:
        question (string): This question as a string
        explantion (string): The explanation for why the correct answer is
            correct.
        num_media_items (int): How many MediaItems should be shown when
            displaying this question
        choices (list of Choice): What Choices this Question has
        datasets (list of Dataset): Which Datasets this Question can pull
            MediaItems from. If this is empty, this Question can use MediaItems
            from any Dataset.
    """

    question = db.Column(db.Text, nullable=False, info={"label":
                                                        "Question"})
    explanation = db.Column(db.Text, info={"label": "Explanation"})
    num_media_items = db.Column(db.Integer,
                                nullable=False,
                                info={
                                    "label": "Number of media items to show"
                                })

    choices = db.relationship("Choice", back_populates="question",
                              info={"import_include": False})
    datasets = db.relationship("Dataset", secondary=question_dataset_table,
                               back_populates="questions")

    def import_dict(self, **kwargs):
        if "num_media_items" in kwargs:
            self.num_media_items = kwargs.pop("num_media_items")

        super(Question, self).import_dict(**kwargs)

    __mapper_args__ = {
        'polymorphic_identity': 'question',
    }


class IntegerQuestion(Question):
    """Ask participants to enter an integer, optionally bounded above/below.

    All bounds are inclusive.

    Attributes:
        answer (int): The correct answer to this question
        bounded_below (bool): If True, enforce a lower bound
        lower_bound (int): The minimum possible answer.
        bounded_above (bool): If True, enforce an upper bound
        upper_bound (int): The maximum possible answer.
    """
    class Meta(object):
        """Specify the result class.
        """
        result_class = IntegerQuestionResult

    answer = db.Column(db.Integer(), info={"label": "Correct answer"})
    lower_bound = db.Column(db.Integer, info={"label": "Lower bound"})
    upper_bound = db.Column(db.Integer, info={"label": "Upper bound"})

    def get_score(self, result):
        """If the choice is the answer, one point.
        """
        try:
            return int(result.integer == self.answer)
        except AttributeError:
            return 0

    def is_correct(self, result):
        try:
            return result.integer == self.answer
        except AttributeError:
            return False

    @db.validates('answer')
    def validate_answer(self, _, answer):
        """Ensure answer is within the bounds.
        """
        assert self.lower_bound is None or answer >= self.lower_bound
        assert self.upper_bound is None or answer <= self.upper_bound
        return answer

    __mapper_args__ = {
        'polymorphic_identity': 'question_integer',
    }


class MultipleChoiceQuestion(Question):
    """A MultipleChoiceQuestion has one or more choices that are correct.
    """
    class Meta(object):
        """Define what kind of Result we are looking for.
        """
        result_class = MultipleChoiceQuestionResult

    def get_score(self, result):
        """If this Question was answered, return the point value of this
        choice. Otherwise return 0.
        """
        try:
            return result.choice.points
        except AttributeError:
            return 0

    def is_correct(self, result):
        try:
            return result.choice.correct
        except AttributeError:
            return False

    __mapper_args__ = {
        'polymorphic_identity': 'question_mc',
    }


class SingleSelectQuestion(MultipleChoiceQuestion):
    """A SingleSelectQuestion allows only one Choice to be selected.
    """

    __mapper_args__ = {
        'polymorphic_identity': 'question_mc_singleselect',
    }


class MultiSelectQuestion(MultipleChoiceQuestion):
    """A MultiSelectQuestion allows any number of Choices to be selected.
    """
    class Meta(object):
        """Define what kind of Result we are looking for.
        """
        result_class = MultiSelectQuestionResult

    __mapper_args__ = {
        'polymorphic_identity': 'question_mc_multiselect',
    }


class ScaleQuestion(SingleSelectQuestion):
    """A ScaleQuestion is like a SingleSelectQuestion, but it displays
    its options horizontally. This is useful for "strongly agree/disagree"
    sort of questions.
    """

    __mapper_args__ = {
        'polymorphic_identity': 'question_mc_singleselect_scale',
    }


class FreeAnswerQuestion(Question):
    """A FreeAnswerQuestion allows a Participant to enter an arbitrary answer.
    """
    class Meta(object):
        """Define what kind of Result we are looking for.
        """
        result_class = FreeAnswerQuestionResult

    def get_score(self, result):
        """If this Question was answered, return 1.
        """
        try:
            if result.text:
                return 1
            return 0
        except AttributeError:
            return 0

    def is_correct(self, result):
        try:
            return bool(result.text)
        except AttributeError:
            return False

    __mapper_args__ = {
        'polymorphic_identity': 'question_freeanswer',
    }


class Choice(Base):
    """ A Choice is a string that is a possible answer for a Question.

    Attributes:
        choice (string): The choice as a string.
        label (string): The label for this choice (1,2,3,a,b,c etc)
        correct (bool): "True" if this choice is correct, "False" otherwise
        question (Question): Which Question owns this Choice
        points (int): How many points the Participant gets for picking this
            choice
    """
    choice = db.Column(db.String(200),
                       info={"label": "Choice"})
    label = db.Column(db.String(3),
                      info={"label": "Label"})
    correct = db.Column(db.Boolean,
                        info={"label": "Correct"})
    points = db.Column(db.Integer,
                       info={"label": "Point value of this choice"},
                       default=0)

    question_id = db.Column(db.Integer, db.ForeignKey("activity.id"))
    question = db.relationship("Question", back_populates="choices")


class MediaItem(Base):
    """A MediaItem is any aid to be shown when displaying an assignment. It can
    be text, image, videos, sound, whatever. Specific types should subclass
    this class and define their own fields needed for rendering.

    Attributes:
        name (str): Name for this Media Item
        assignments (list of Assignment): Which Assignments display this
            MediaItem
        dataset (Dataset): Which Dataset owns this MediaItem
    """

    assignments = db.relationship(
        "Assignment",
        secondary=assignment_media_item_table,
        back_populates="media_items")
    dataset = db.relationship("Dataset", back_populates="media_items")
    dataset_id = db.Column(db.Integer, db.ForeignKey("dataset.id"))
    type = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(100), nullable=False,
                     info={"label": "Name"},
                     default="New media item")

    __mapper_args__ = {
        'polymorphic_identity': 'media_item',
        'polymorphic_on': type
    }


class Graph(MediaItem):
    """A Graph is an image file located on the server that may be shown in
    conjunction with an Assignment.

    Attributes:
        path (str): Absolute path to this Graph on disk
    """

    path = db.Column(db.String(200), nullable=False)

    def filename(self):
        """Return the filename of this graph.
        """
        return os.path.split(os.path.basename(self.path))[1]

    __mapper_args__ = {
        'polymorphic_identity': 'graph'
    }


class Text(MediaItem):
    """Text is simply a piece of text that can be used as a MediaItem.

    Attributes:
        text (str): The text of this media item.
    """

    text = db.Column(db.Text, info={"label": "Text"})

    __mapper_args__ = {
        'polymorphic_identity': 'text'
    }


class ScorecardSettings(Base):
    """A ScorecardSettings object represents the configuration of some kind of
    scorecard.

    Scorecards may be shown after each Activity or after each Experiment (or
    both). Since the configuration of the two scorecards is identical, it has
    been refactored to this class.

    Attributes:
        display_scorecard (bool): Whether or not to display this scorecard at
            all.
        display_score (bool): Whether or not to display a tally of points.
        display_time (bool): Whether or not to display a count of how much time
            elapsed.
        display_correctness (bool): Whether or not to display correctness
            grades.
        display_feedback (bool): Whether or not to display feedback on
            responses.
    """

    display_scorecard = db.Column(db.Boolean,
                                  info={"label": "Display scorecards"})
    display_score = db.Column(db.Boolean,
                              info={"label": "Display points on scorecard"})
    display_time = db.Column(db.Boolean,
                             info={"label": "Display time on scorecard"})
    display_correctness = db.Column(db.Boolean,
                                    info={"label":
                                          "Display correctness on scorecard"})
    display_feedback = db.Column(db.Boolean,
                                 info={"label":
                                       "Display feedback on scorecard"})


class Experiment(Base):
    """An Experiment contains a list of Activities.

    Attributes:
        name (string
        created (datetime
        start (datetime): When this experiment becomes accessible for answers
        stop (datetime): When this experiment stops accepting answers
        activities (list of Activity): What Activities are included in this
            Experiment's AssignmentSets
        assignment_sets (list of ParticiapntExperiment): List of
            AssignmentSets that are associated with this Experiment
        disable_previous (bool): If True, don't allow Participants to view and
            modify previous activities.
        show_timers (bool): If True, display a timer on each activity
            expressing how long the user has been viewing this activity.
        show_scores (bool): If True, show the participant a cumulative score on
            every activity.
        scorecard_settings (ScorecardSettings): A ScorecardSettings instance
            that determines how scorecards will be rendered in this Experiment.

            If the ``display_scorecard`` field is ``False``, then no scorecards
            will be displayed.

            If the ``display_scorecard`` field is ``True``, then scorecards
            will be displayed after Activities whose own ``ScorecardSettings``
            objects specify that scorecards should be shown. They will be
            rendered according to the ``ScorecardSettings`` of that Activity.

            In addition, a scorecard will be rendered after the experiment
            according to the Experiment's ``ScorecardSettings``.
        flash (bool): If True, flash the MediaItem for flash_duration
        milliseconds
        flash_duration (int): How long to display the MediaItem in milliseconds
    """

    name = db.Column(db.String(150), index=True, nullable=False,
                     info={"label": "Name"})
    created = db.Column(db.DateTime, info={"import_include": False})
    start = db.Column(db.DateTime, nullable=False, info={"label": "Start"})
    stop = db.Column(db.DateTime, nullable=False, info={"label": "Stop"})
    blurb = db.Column(db.Text, info={"label": "Blurb"})
    show_scores = db.Column(db.Boolean,
                            info={"label": ("Show score tally during the"
                                            " experiment")})
    flash = db.Column(db.Boolean,
                      info={"label": "Flash MediaItems when displaying"})
    flash_duration = db.Column(db.Integer, nullable=False, default=0,
                               info={"label": "Flash duration (ms)"})
    disable_previous = db.Column(db.Boolean,
                                 info={"label": ("Don't let participants go "
                                                 "back after submitting an "
                                                 "activity")})
    show_timers = db.Column(db.Boolean,
                            info={"label": "Show timers on activities"})

    assignment_sets = db.relationship("AssignmentSet",
                                      back_populates="experiment",
                                      info={"import_include": False})

    scorecard_settings_id = db.Column(db.Integer,
                                      db.ForeignKey("scorecard_settings.id"))
    scorecard_settings = db.relationship("ScorecardSettings",
                                         uselist=False,
                                         info={"import_include": False})

    def __init__(self, *args, **kwargs):
        """Make sure to populate scorecard_settings.
        """
        self.scorecard_settings = ScorecardSettings()
        super(Experiment, self).__init__(*args, **kwargs)

    @property
    def running(self):
        """Returns True if this experiment is currently running, otherwise
        False.
        """
        now = datetime.now()
        return now >= self.start and now <= self.stop


class Dataset(Base):
    """A Dataset represents some data that MediaItems are based on.

    Attributes:
        name (string): The name of this dataset.
        info (string): Some information about this dataset
        media_items (list of MediaItem): Which MediaItems this Dataset owns
        questions (list of Questions): Which Questions reference this Dataset
    """
    name = db.Column(db.String(100), nullable=False, info={"label": "Name"})
    info = db.Column(db.Text, info={"label": "Info"})

    media_items = db.relationship("MediaItem", back_populates="dataset")
    questions = db.relationship("Question", secondary=question_dataset_table,
                                back_populates="datasets")
