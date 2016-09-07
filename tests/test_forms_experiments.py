"""Test activity forms.
"""
import pytest

from quizApp.forms import experiments as experiment_forms
from quizApp import models, db
from tests import factories


def test_question_form():
    question_form = experiment_forms.QuestionForm()

    with pytest.raises(NotImplementedError):
        question_form.populate_from_question(None)

    with pytest.raises(NotImplementedError):
        question_form.populate_from_result(None)

    with pytest.raises(NotImplementedError):
        question_form.result


def test_integer_answer_form(client):
    form = experiment_forms.IntegerAnswerForm()
    question = factories.IntegerQuestionFactory()

    question.upper_bound = 5
    question.save()

    form.populate_from_question(question)

    form.integer.data = 6

    assert not form.validate()

    form.integer.data = 4

    assert form.validate()

    question.lower_bound = 2
    db.session.commit()
    form.populate_from_question(question)

    form.integer.data = 1

    assert not form.validate()

    result = models.IntegerQuestionResult(integer=4)

    form.populate_from_result(result)

    assert form.integer.default == result.integer

    assert form.result.integer == result.integer


def test_free_answer_form(client):
    form = experiment_forms.FreeAnswerForm()
    question = factories.FreeAnswerQuestionFactory()

    form.populate_from_question(question)  # noop

    result = models.FreeAnswerQuestionResult(text="foo")

    form.populate_from_result(result)

    assert form.text.default == result.text

    assert form.result.text == result.text
