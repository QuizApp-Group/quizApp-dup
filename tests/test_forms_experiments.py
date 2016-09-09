"""Test activity forms.
"""
import pytest

from quizApp.forms import experiments as experiment_forms
from quizApp import models, db
from tests import factories


def test_activity_answer_form(client):
    activity_answer_form = experiment_forms.ActivityAnswerForm()

    with pytest.raises(NotImplementedError):
        activity_answer_form.populate_from_activity(None)

    with pytest.raises(NotImplementedError):
        activity_answer_form.populate_from_result(None)

    with pytest.raises(NotImplementedError):
        activity_answer_form.result


def test_scorecard_answer_form(client):
    form = experiment_forms.ScorecardAnswerForm()

    form.populate_from_result(None)  # noop
    assert form.result


def test_integer_answer_form(client):
    form = experiment_forms.IntegerAnswerForm()
    question = factories.IntegerQuestionFactory()

    question.upper_bound = 5
    question.save()

    form.populate_from_activity(question)

    form.integer.data = 6

    assert not form.validate()

    form.integer.data = 4

    assert form.validate()

    question.lower_bound = 2
    db.session.commit()
    form.populate_from_activity(question)

    form.integer.data = 1

    assert not form.validate()

    result = models.IntegerQuestionResult(integer=4)
    form.populate_from_result(result)
    form.integer.data = 4

    assert form.integer.default == result.integer
    assert form.result.integer == result.integer


def test_free_answer_form(client):
    form = experiment_forms.FreeAnswerForm()
    question = factories.FreeAnswerQuestionFactory()

    form.populate_from_activity(question)  # noop

    result = models.FreeAnswerQuestionResult(text="foo")

    form.populate_from_result(result)

    assert form.text.default == result.text

    form.text.data = result.text

    assert form.result.text == result.text
