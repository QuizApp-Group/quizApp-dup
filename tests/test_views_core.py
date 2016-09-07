"""Tests for core views.
"""
from __future__ import unicode_literals

from tests.auth import login_experimenter, login_participant


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
    assert "Experiment List" in data
