"""Tests for core views.
"""
from __future__ import unicode_literals

from quizApp import models
from tests.auth import login_experimenter, login_participant
from tests import factories


def test_getting_started(client, users):
    login_experimenter(client)
    url = "/getting_started"

    response = client.get(url)

    assert response.status_code == 200


def test_post_login(client, users):
    login_experimenter(client)
    url = "/post_login"

    response = client.get(url, follow_redirects=True)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert "readthedocs" in data

    login_participant(client)
    response = client.get(url, follow_redirects=True)
    data = response.data.decode(response.charset)

    assert response.status_code == 200


def test_auto_register(client, users):
    experiment = factories.create_experiment(1, 1)
    experiment.assignment_sets[0].progress = 0
    experiment.save()
    initial_num_users = models.Participant.query.count()
    url = "/auto_register?experiment_id=" + str(experiment.id)

    response = client.get(url, follow_redirects=True)
    data = response.data.decode(response.charset)

    assert response.status_code == 200
    assert experiment.blurb in data
    assert models.Participant.query.count() == 1 + initial_num_users

    response = client.get(url, follow_redirects=True)
    data = response.data.decode(response.charset)

    assert response.status_code == 200
    assert experiment.blurb in data
    assert models.Participant.query.count() == 1 + initial_num_users
