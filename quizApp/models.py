"""Models for the quizApp.
"""
import os

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
        for key, value in kwargs.items():
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
        participant_experiments (list of ParticipantExperiments): List of
            ParticipantExperiments that this participant has
    """

    opt_in = db.Column(db.Boolean)
    foreign_id = db.Column(db.String(100))

    assignments = db.relationship("Assignment", back_populates="participant")
    experiments = db.relationship("ParticipantExperiment",
                                  back_populates="participant")

    __mapper_args__ = {
        'polymorphic_identity': 'participant',
    }


class ParticipantExperiment(Base):
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
                                 back_populates="participant_experiments")

    assignments = db.relationship("Assignment",
                                  back_populates="participant_experiment",
                                  info={"import_include": False})

    @db.validates('assignments')
    def validate_assignments(self, _, assignment):
        """The Assignments in this model must be related to the same Experiment
        as this model is."""
        assert assignment.experiment == self.experiment
        assert assignment.participant == self.participant
        assert assignment.activity in self.experiment.activities or \
            not assignment.activity
        return assignment

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
        media_items (list of MediaItem): What MediaItems should be shown
        participant (Participant): Which Participant gets this Assignment
        activity (Activity): Which Activity this Participant should see
        choice (Choice): Which Choice this Participant chose as their answer
        participant_experiment (ParticipantExperiment): Which
            ParticipantExperiment this Assignment belongs to
    """

    skipped = db.Column(db.Boolean, info={"import_include": False})
    comment = db.Column(db.String(200), info={"import_include": False})
    choice_order = db.Column(db.String(80), info={"import_include": False})

    media_items = db.relationship("MediaItem",
                                  secondary=assignment_media_item_table,
                                  back_populates="assignments",
                                  info={"import_include": True})

    participant_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    participant = db.relationship("Participant", back_populates="assignments",
                                  info={"import_include": False})

    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"))
    activity = db.relationship("Activity", back_populates="assignments",
                               info={"import_include": False})

    choice_id = db.Column(db.Integer, db.ForeignKey("choice.id"))
    choice = db.relationship("Choice", back_populates="assignments",
                             info={"import_include": False})

    experiment_id = db.Column(db.Integer, db.ForeignKey("experiment.id"))
    experiment = db.relationship("Experiment", back_populates="assignments",
                                 info={"import_include": False})

    participant_experiment_id = db.Column(
        db.Integer,
        db.ForeignKey("participant_experiment.id"))
    participant_experiment = db.relationship("ParticipantExperiment",
                                             back_populates="assignments")

    def import_dict(self, **kwargs):
        """If we are setting assignments, we need to update experiments to
        match.
        """
        if "experiments" not in kwargs:
            participant_experiment = kwargs.pop("participant_experiment")
            if participant_experiment.experiment:
                self.experiment = participant_experiment.experiment
            self.participant_experiment = participant_experiment

        super(Assignment, self).import_dict(**kwargs)

    @db.validates("activity")
    def validate_activity(self, _, activity):
        """Make sure that the activity is part of this experiment.
        Make sure that the number of media items on the activity is the same as
        the number of media items this assignment has.
        """
        assert self.experiment in activity.experiments

        try:
            assert (activity.num_media_items == len(self.media_items)) or \
                activity.num_media_items == -1
        except AttributeError:
            pass

        return activity

    @db.validates("choice")
    def validate_choice(self, _, choice):
        """This must be a valid choice, i.e. contained in the question (if any)
        """
        if "question" in self.activity.type and choice is not None:
            assert choice in self.activity.choices

        return choice


activity_experiment_table = db.Table(
    "activity_experiment", db.metadata,
    db.Column("activity_id", db.Integer, db.ForeignKey('activity.id')),
    db.Column('experiment_id', db.Integer, db.ForeignKey('experiment.id'))
)


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
        category (string): A description of this assignment's category, for the
            users' convenience.
        experiments (list of Experiment): What Experiments include this
            Activity
        assignments (list of Assignment): What Assignments include this
            Activity
    """

    type = db.Column(db.String(50), nullable=False)
    experiments = db.relationship("Experiment",
                                  secondary=activity_experiment_table,
                                  back_populates="activities",
                                  info={"import_include": False})

    assignments = db.relationship("Assignment", back_populates="activity",
                                  cascade="all")
    category = db.Column(db.String(100), info={"label": "Category"})

    def import_dict(self, **kwargs):
        """If we are setting assignments, we need to update experiments to
        match.
        """
        if "experiments" not in kwargs:
            assignments = kwargs.pop("assignments")
            for assignment in assignments:
                if assignment.experiment:
                    self.experiments.append(assignment.experiment)
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


class Question(Activity):
    """A Question is related to one or more MediaItems and has one or more Choices,
    and is a part of one or more Experiments.

    Attributes:
        question (string): This question as a string
        explantion (string): The explanation for why the correct answer is
            correct.
        needs_comment (bool): True if the participant should be asked why
            they picked what they did after they answer the question.
        num_media_items (int): How many MediaItems should be shown when
            displaying this question
        choices (list of Choice): What Choices this Question has
        datasets (list of Dataset): Which Datasets this Question can pull
            MediaItems from. If this is empty, this Question can use MediaItems
            from any Dataset.
    """

    question = db.Column(db.String(200), nullable=False, info={"label":
                                                               "Question"})
    explanation = db.Column(db.String(200), info={"label": "Explanation"})
    num_media_items = db.Column(db.Integer,
                                nullable=False,
                                info={
                                    "label": "Number of media items to show"
                                })
    needs_comment = db.Column(db.Boolean(), info={"label": "Allow comments"})

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


class MultipleChoiceQuestion(Question):
    """A MultipleChoiceQuestion has one or more choices that are correct.
    """
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
        assignment (Assignment): Which Assignments had Participants pick this
            Choice as the correct answer
    """
    choice = db.Column(db.String(200), nullable=False,
                       info={"label": "Choice"})
    label = db.Column(db.String(3),
                      info={"label": "Label"})
    correct = db.Column(db.Boolean,
                        info={"label": "Correct?"})

    question_id = db.Column(db.Integer, db.ForeignKey("activity.id"))
    question = db.relationship("Question", back_populates="choices")

    assignments = db.relationship("Assignment", back_populates="choice",
                                  info={"import_include": False})


class MediaItem(Base):
    """A MediaItem is any aid to be shown when displaying an assignment. It can
    be text, image, videos, sound, whatever. Specific types should subclass
    this class and define their own fields needed for rendering.

    Attributes:
        flash (bool): If True, flash the MediaItem for flash_duration
        milliseconds
        flash_duration (int): How long to display the MediaItem in milliseconds
        name (str): Name for this Media Item
        assignments (list of Assignment): Which Assignments display this
            MediaItem
        dataset (Dataset): Which Dataset owns this MediaItem
    """

    assignments = db.relationship(
        "Assignment",
        secondary=assignment_media_item_table,
        back_populates="media_items")
    flash = db.Column(db.Boolean,
                      info={"label": "Flash this MediaItem when displaying?"})
    flash_duration = db.Column(db.Integer, nullable=False, default=-1,
                               info={"label": "Flash duration (ms)"})
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


class Experiment(Base):
    """An Experiment contains a list of Activities.

    Attributes:
        name (string
        created (datetime
        start (datetime): When this experiment becomes accessible for answers
        stop (datetime): When this experiment stops accepting answers
        activities (list of Activity): What Activities are included in this
            Experiment's ParticipantExperiments
        participant_experiments (list of ParticiapntExperiment): List of
            ParticipantExperiments that are associated with this Experiment
        assignments (list of Assignment): Assignments that are present in this
            Experiment's ParticipantExperiments
    """

    name = db.Column(db.String(150), index=True, nullable=False,
                     info={"label": "Name"})
    created = db.Column(db.DateTime, info={"import_include": False})
    start = db.Column(db.DateTime, nullable=False, info={"label": "Start"})
    stop = db.Column(db.DateTime, nullable=False, info={"label": "Stop"})
    blurb = db.Column(db.String(500), info={"label": "Blurb"})

    activities = db.relationship("Activity",
                                 secondary=activity_experiment_table,
                                 back_populates="experiments",
                                 info={"import_include": False})

    participant_experiments = db.relationship("ParticipantExperiment",
                                              back_populates="experiment",
                                              info={"import_include": False})

    assignments = db.relationship("Assignment", back_populates="experiment",
                                  info={"import_include": False})


class Dataset(Base):
    """A Dataset represents some data that MediaItems are based on.

    Attributes:
        name (string): The name of this dataset.
        uri (string): A path or descriptor of where this dataset is located.
        media_items (list of MediaItem): Which MediaItems this Dataset owns
        questions (list of Questions): Which Questions reference this Dataset
    """
    name = db.Column(db.String(100), nullable=False, info={"label": "Name"})
    uri = db.Column(db.String(200), info={"label": "URI"})

    media_items = db.relationship("MediaItem", back_populates="dataset")
    questions = db.relationship("Question", secondary=question_dataset_table,
                                back_populates="datasets")
