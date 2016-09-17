"""Tests for view helpers.
"""
from __future__ import unicode_literals

from mock import MagicMock, patch
from wtforms import Form

from tests.auth import login_participant, get_participant
from tests.factories import create_experiment, ExperimentFactory
from tests.helpers import json_success
from quizApp.models import Base
from quizApp.views.helpers import validate_model_id,\
    get_or_create_assignment_set, get_first_assignment,\
    validate_form_or_error, experiment_to_url_code, url_code_to_experiment


def test_get_first_assignment(client, users):
    login_participant(client)
    experiment = create_experiment(1, 1)
    assignment_set = experiment.assignment_sets[0]
    assignment_set.complete = True
    assignment_set.participant = get_participant()
    experiment.save()

    result = get_first_assignment(experiment)
    assert result == assignment_set.assignments[0]

    experiment = create_experiment(0, 0)
    experiment.save()
    result = get_first_assignment(experiment)
    assert result is None


def test_get_or_create_assignment_set(client, users):
    login_participant(client)
    experiment = create_experiment(1, 1)
    experiment.assignment_sets = []
    experiment.save()

    result = get_or_create_assignment_set(experiment)
    assert result is None


@patch('quizApp.views.helpers.abort', autospec=True)
def test_validate_model_id(abort_mock):
    """Test the validate_model_id method.
    """
    obj_class_mock = MagicMock(spec_set=Base)
    attrs = {"query.get.return_value": None}
    obj_class_mock.configure_mock(**attrs)

    validate_model_id(obj_class_mock, 5)
    abort_mock.assert_called_once()


def test_validate_form_or_error():
    form = MagicMock(autospec=Form())

    form.validate.return_value = False
    form.errors = ""

    result = validate_form_or_error(form)
    assert not json_success(result.data)

    form.validate.return_value = True
    result = validate_form_or_error(form)
    assert result is None


@patch('quizApp.views.helpers.abort', autospec=True)
def test_url_code_to_experiment(abort_mock, client):
    experiment = ExperimentFactory(name="foo bar !?baz")
    experiment.save()

    code = experiment_to_url_code(experiment)
    decoded_exp = url_code_to_experiment(code)

    assert experiment == decoded_exp

    bad_experiment = ExperimentFactory(id=experiment.id, name="other name")
    code = experiment_to_url_code(bad_experiment)
    decoded_exp = url_code_to_experiment(code)
    abort_mock.assert_called_once()
