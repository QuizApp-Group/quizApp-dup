"""Run tests on the database models.
"""
from __future__ import unicode_literals
import os

import pytest
from sqlalchemy import inspect

from tests.factories import ExperimentFactory, ParticipantFactory, \
    ChoiceFactory, QuestionFactory
from quizApp.models import AssignmentSet, Assignment, Role, Activity, \
    Question, Graph, MultipleChoiceQuestionResult, MultipleChoiceQuestion, \
    FreeAnswerQuestion, FreeAnswerQuestionResult, Result, \
    IntegerQuestionResult, IntegerQuestion


def test_db_rollback1():
    """Along with test_db_rollback2, ensure rollbacks are working correctly.
    """
    exp = Role(name="notaname-1")
    exp.save()
    assert Role.query.filter_by(name="notaname-1").count() == 1
    assert Role.query.filter_by(name="notaname-2").count() == 0


def test_db_rollback2():
    """Along with test_db_rollback1, ensure rollbacks are working correctly.
    """
    exp = Role(name="notaname-2")
    exp.save()
    assert Role.query.filter_by(name="notaname-1").count() == 0
    assert Role.query.filter_by(name="notaname-2").count() == 1


def test_assignment_set_validators():
    """Make sure validators are functioning correctly.
    """
    exp1 = ExperimentFactory()
    exp2 = ExperimentFactory()

    assignment_set = AssignmentSet(experiment=exp1)
    assignment = Assignment()

    part1 = ParticipantFactory()
    part2 = ParticipantFactory()
    part1.save()
    part2.save()

    assignment_set.experiment = exp2
    assignment_set.participant = part1
    assignment.participant = part2

    with pytest.raises(AssertionError):
        assignment_set.assignments.append(assignment)

    activity = Activity()
    exp2.activities.append(activity)
    assignment.activity = activity
    assignment_set.participant = part2

    assignment_set.assignments.append(assignment)


def test_assignment_validators():
    """Test validators of the Assignment model.
    """
    assn = Assignment()
    exp = ExperimentFactory()
    activity = Activity()
    assn.experiment = exp
    activity.num_media_items = -1

    choice = ChoiceFactory()
    question = Question()
    question.num_media_items = -1

    question.experiments.append(exp)

    assn.activity = question
    result = MultipleChoiceQuestionResult()
    result.choice = choice

    with pytest.raises(AssertionError):
        assn.result = result

    question.choices.append(choice)

    assn.result = result

    # Test the media item number validations
    question2 = QuestionFactory()
    question2.experiments.append(exp)
    question2.num_media_items == len(assn.media_items) + 1

    with pytest.raises(AssertionError):
        assn.activity = question2

    question2.num_media_items = -1
    assn.activity = question2

    question2.num_media_items = len(assn.media_items)
    assn.activity = question2


def test_result_validators():
    """Test for various result validators.
    """
    # Make sure types are correct
    choice = ChoiceFactory()
    mc_question = MultipleChoiceQuestion(num_media_items=-1)
    mc_result = MultipleChoiceQuestionResult(choice=choice)
    fa_question = FreeAnswerQuestion(num_media_items=-1)
    fa_result = FreeAnswerQuestionResult()
    assignment = Assignment()

    experiment = ExperimentFactory()
    assignment.experiment = experiment
    mc_question.experiments.append(experiment)

    assignment.activity = mc_question

    with pytest.raises(AssertionError):
        assignment.result = mc_result

    mc_question.choices.append(choice)
    assignment.result = mc_result

    assignment = Assignment()
    assignment.experiment = experiment
    mc_question.experiments.append(experiment)
    assignment.activity = mc_question

    with pytest.raises(AssertionError):
        assignment.result = fa_result

    assignment = Assignment()
    assignment.experiment = experiment
    fa_question.experiments.append(experiment)
    assignment.activity = fa_question

    with pytest.raises(AssertionError):
        assignment.result = mc_result


def test_graph_filename():
    """Make sure graph filenames work correctly.
    """
    path = "/foo/bar/baz/"
    filename = "boo.png"

    full_path = os.path.join(path, filename)

    graph = Graph(path=full_path, name="Foobar")

    assert graph.filename() == filename


def test_save():
    """Make sure saving works correctly.
    """
    role = Role(name="Foo")

    role.save()

    inspection = inspect(role)

    assert not inspection.pending

    role2 = Role(name="bar")

    role2.save(commit=False)

    inspection = inspect(role2)

    assert inspection.pending


def test_activity_get_score():
    activity = Activity()
    result = Result()
    with pytest.raises(NotImplementedError):
        score = activity.get_score(result)


def test_free_answer_question_get_score():
    fa_question = FreeAnswerQuestion()
    fa_result = FreeAnswerQuestionResult()

    assert fa_question.get_score(fa_result) == 0

    fa_result.text = "AAAA"

    assert fa_question.get_score(fa_result) == 1


def test_assignment_get_score():
    assignment = Assignment()

    with pytest.raises(AttributeError):
        assert assignment.get_score() is None


def test_integer_question_validators():
    int_question = IntegerQuestion()
    int_result = IntegerQuestionResult()

    int_question.lower_bound = 1

    with pytest.raises(AssertionError):
        int_question.answer = 0

    int_question.answer = 1
    int_question.upper_bound = 2

    with pytest.raises(AssertionError):
        int_question.answer = 3

    int_question.answer = 2

    int_result.integer = 2

    assert int_question.get_score(int_result) == 1

    int_result.integer = 1

    assert int_question.get_score(int_result) == 0
