"""Tests for view helpers.
"""
from __future__ import unicode_literals

from mock import MagicMock, patch

from tests.auth import login_participant, get_participant
from tests.factories import create_experiment
from quizApp.models import Base
from quizApp.views.helpers import validate_model_id,\
    get_or_create_participant_experiment, get_first_assignment


def test_get_first_assignment(client, users):
    login_participant(client)
    experiment = create_experiment(1, 1)
    participant_experiment = experiment.participant_experiments[0]
    participant_experiment.complete = True
    participant_experiment.participant = get_participant()
    experiment.save()

    result = get_first_assignment(experiment)
    assert result == participant_experiment.assignments[0]

    experiment = create_experiment(0, 0)
    experiment.save()
    result = get_first_assignment(experiment)
    assert result is None


def test_get_or_create_participant_experiment(client, users):
    login_participant(client)
    experiment = create_experiment(1, 1)
    experiment.participant_experiments = []
    experiment.save()

    result = get_or_create_participant_experiment(experiment)
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
