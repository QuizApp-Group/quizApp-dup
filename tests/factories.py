"""Various factories, useful for writing less boilerplate when testing.
"""
import random

import factory
from quizApp import models
from datetime import datetime, timedelta


class ExperimentFactory(factory.Factory):
    class Meta:
        model = models.Experiment

    name = factory.Faker('name')
    blurb = factory.Faker('text')
    start = datetime.now()
    stop = datetime.now() + timedelta(days=5)


class ParticipantFactory(factory.Factory):
    class Meta:
        model = models.Participant

    email = factory.Faker('email')
    password = factory.Faker('password')


class ChoiceFactory(factory.Factory):
    class Meta:
        model = models.Choice

    choice = factory.Faker('text')
    label = factory.Iterator(['a', 'b', 'c', 'd'])
    correct = factory.Faker("boolean")


class ActivityFactory(factory.Factory):
    class Meta:
        model = models.Activity

    category = factory.Faker("text")


class QuestionFactory(ActivityFactory):
    class Meta:
        model = models.Question

    question = factory.Faker("text")
    num_media_items = factory.Faker("pyint")
    explanation = factory.Faker("text")

    @factory.post_generation
    def choices(self, create, extracted, **kwargs):
        if len(self.choices):
            return

        for i in xrange(0, 4):
            self.choices.append(ChoiceFactory())

    @factory.post_generation
    def datasets(self, create, extracted, **kwargs):
        if len(self.datasets):
            return

        for i in xrange(0, 4):
            self.datasets.append(DatasetFactory())


class SingleSelectQuestionFactory(QuestionFactory):
    class Meta:
        model = models.SingleSelectQuestion


class ScaleQuestionFactory(QuestionFactory):
    class Meta:
        model = models.ScaleQuestion


class AssignmentFactory(factory.Factory):
    class Meta:
        model = models.Assignment

    skipped = factory.Faker("boolean")
    comment = factory.Faker("text")
    choice_order = factory.Faker("text")


class ParticipantExperimentFactory(factory.Factory):
    class Meta:
        model = models.ParticipantExperiment

    progress = factory.Faker("pyint")
    complete = factory.Faker("boolean")


class MediaItemFactory(factory.Factory):
    class Meta:
        model = models.MediaItem

    name = factory.Faker("text", max_nb_chars=100)


class GraphFactory(MediaItemFactory):
    class Meta:
        model = models.Graph

    path = factory.Faker("file_name")


class DatasetFactory(factory.Factory):
    class Meta:
        model = models.Dataset

    name = factory.Faker("text", max_nb_chars=100)
    uri = factory.Faker("uri")

    @factory.post_generation
    def media_items(self, create, extracted, **kwargs):
        if len(self.media_items):
            return

        for i in xrange(0, 4):
            self.media_items.append(MediaItemFactory())


def create_experiment(num_activities, participants, activity_types=[]):
    experiment = ExperimentFactory()
    num_participants = len(participants)
    participant_experiments = []

    for participant in participants:
        part_exp = ParticipantExperimentFactory()
        part_exp.participant = participant
        part_exp.experiment = experiment
        participant_experiments.append(part_exp)

    for i in xrange(0, num_activities*num_participants):
        participant = participants[i % num_participants]
        part_exp = participant_experiments[i % num_participants]

        if activity_types:
            activity_type = random.choice(activity_types)
            if "scale" in activity_type:
                activity = ScaleQuestionFactory()
            elif "singleselect" in activity_type:
                activity = SingleSelectQuestionFactory()
        else:
            activity = ActivityFactory()

        activity.num_media_items = -1
        assignment = AssignmentFactory()

        activity.experiments.append(experiment)

        assignment.experiment = experiment
        assignment.participant = participant
        assignment.activity = activity

        part_exp.assignments.append(assignment)

    return experiment
