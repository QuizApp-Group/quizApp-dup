"""Various factories, useful for writing less boilerplate when testing.
"""
from __future__ import unicode_literals
from builtins import range
from builtins import object
import random

import factory
from quizApp import models
from datetime import datetime, timedelta


class ExperimentFactory(factory.Factory):
    class Meta(object):
        model = models.Experiment

    name = factory.Faker('name')
    blurb = factory.Faker('text')
    start = datetime.now() - timedelta(days=5)
    stop = datetime.now() + timedelta(days=5)


class UserFactory(factory.Factory):
    class Meta(object):
        model = models.User

    email = factory.Faker('email')
    password = factory.Faker('password')


class ParticipantFactory(factory.Factory):
    class Meta(object):
        model = models.Participant

    email = factory.Faker('email')
    password = factory.Faker('password')


class ChoiceFactory(factory.Factory):
    class Meta(object):
        model = models.Choice

    choice = factory.Faker('text')
    label = factory.Iterator(['a', 'b', 'c', 'd'])
    correct = factory.Faker("boolean")
    points = factory.Faker('pyint')


class ActivityFactory(factory.Factory):
    class Meta(object):
        model = models.Activity

    category = factory.Faker("text")
    include_in_scorecards = factory.Faker('boolean')


class ScorecardFactory(ActivityFactory):
    class Meta(object):
        model = models.Scorecard

    title = factory.Faker("text")
    prompt = factory.Faker('text')


class QuestionFactory(ActivityFactory):
    class Meta(object):
        model = models.Question

    question = factory.Faker("text")
    num_media_items = factory.Faker("pyint")
    explanation = factory.Faker("text")

    @factory.post_generation
    def choices(self, create, extracted, **kwargs):
        if len(self.choices):
            return

        for i in range(0, 4):
            self.choices.append(ChoiceFactory())

    @factory.post_generation
    def datasets(self, create, extracted, **kwargs):
        if len(self.datasets):
            return

        for i in range(0, 4):
            self.datasets.append(DatasetFactory())


class FreeAnswerQuestionFactory(QuestionFactory):
    class Meta(object):
        model = models.FreeAnswerQuestion


class IntegerQuestionFactory(QuestionFactory):
    class Meta(object):
        model = models.IntegerQuestion


class SingleSelectQuestionFactory(QuestionFactory):
    class Meta(object):
        model = models.SingleSelectQuestion


class ScaleQuestionFactory(QuestionFactory):
    class Meta(object):
        model = models.ScaleQuestion


class MultiSelectQuestionFactory(QuestionFactory):
    class Meta(object):
        model = models.MultiSelectQuestion


class AssignmentFactory(factory.Factory):
    class Meta(object):
        model = models.Assignment

    comment = factory.Faker("text")
    choice_order = factory.Faker("text")


class AssignmentSetFactory(factory.Factory):
    class Meta(object):
        model = models.AssignmentSet

    progress = factory.Faker("pyint")
    complete = factory.Faker("boolean")


class MediaItemFactory(factory.Factory):
    class Meta(object):
        model = models.MediaItem

    name = factory.Faker("text", max_nb_chars=100)


class GraphFactory(MediaItemFactory):
    class Meta(object):
        model = models.Graph

    path = factory.Faker("file_name")


class DatasetFactory(factory.Factory):
    class Meta(object):
        model = models.Dataset

    name = factory.Faker("text", max_nb_chars=100)
    info = factory.Faker("text")

    @factory.post_generation
    def media_items(self, create, extracted, **kwargs):
        if len(self.media_items):
            return

        for i in range(0, 4):
            self.media_items.append(MediaItemFactory())


class IntegerQuestionResultFactory(factory.Factory):
    class Meta(object):
        model = models.IntegerQuestionResult

    integer = factory.Faker("pyint")


class FreeAnswerQuestionResultFactory(factory.Factory):
    class Meta(object):
        model = models.FreeAnswerQuestionResult

    text = factory.Faker("text")


def create_result(activity):
    """Create a result for the given activity.
    """
    factory_mapping = {
        "question_mc_singleselect": models.MultipleChoiceQuestionResult,
        "question_mc_singleselect_scale": models.MultipleChoiceQuestionResult,
        "question_mc_multiselect": models.MultiSelectQuestionResult,
        "question_integer": IntegerQuestionResultFactory,
        "question_freeanswer": FreeAnswerQuestionFactory,
        "scorecard": models.ScorecardResult,
    }

    result = factory_mapping[activity.type]()

    if "question_mc_singleselect" in activity.type:
        result.choice = random.choice(activity.choices)

    if "question_mc_multiselect" == activity.type:
        result.choices = [random.choice(activity.choices)]

    return result


def create_experiment(num_activities, num_participants, activity_types=[]):
    experiment = ExperimentFactory()
    assignment_sets = []

    for _ in range(0, num_participants):
        assignment_set = AssignmentSetFactory()
        experiment.assignment_sets.append(assignment_set)
        assignment_sets.append(assignment_set)

    for i in range(0, num_activities*num_participants):
        assignment_set = assignment_sets[i % num_participants]

        if activity_types:
            activity_type = random.choice(activity_types)
            factory_mapping = {
                "question_mc_singleselect": SingleSelectQuestionFactory,
                "question_mc_singleselect_scale": ScaleQuestionFactory,
                "question_integer": IntegerQuestionFactory,
                "question_freeanswer": FreeAnswerQuestionFactory,
                "question_mc_multiselect": MultiSelectQuestionFactory,
                "scorecard": ScorecardFactory,
            }
            activity = factory_mapping[activity_type]()
        else:
            activity = ActivityFactory()

        activity.num_media_items = -1
        assignment = AssignmentFactory()

        assignment.experiment = experiment
        assignment.activity = activity

        assignment_set.assignments.append(assignment)

    return experiment
