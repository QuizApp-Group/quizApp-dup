"""Test amazon turk views.
"""
from __future__ import unicode_literals
import mock
from flask import session

from quizApp.models import Participant
from quizApp.views import mturk
from tests.factories import create_experiment


def test_register(client, users):
    experiment = create_experiment(1, 1)
    experiment.assignment_sets[0].complete = False
    experiment.assignment_sets[0].progress = 0
    experiment.save()

    response = client.get("/mturk/register?experiment_id={}".
                          format(experiment.id))
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert experiment.blurb in data

    response = client.get("/mturk/register")
    assert response.status_code == 400

    response = client.get(("/mturk/register?experiment_id={}"
                           "&workerId=4fsa&assignmentId=4&turkSubmitTo=4"
                           "&hitId=5").
                          format(experiment.id))

    assert response.status_code == 200
    data = response.data.decode(response.charset)
    assert "/experiments/{}/assignments/".format(experiment.id) in \
        data

    # one from users fixture, one from views
    assert Participant.query.count() == 2

    response = client.get(("/mturk/register?experiment_id={}"
                           "&workerId=4fsa&assignmentId=4&turkSubmitTo=4"
                           "&hitId=5").
                          format(experiment.id))
    data = response.data.decode(response.charset)
    assert "mturk/externalSubmit" in session["mturk_post_url"]

    assert "/experiments/{}/assignments/".format(experiment.id) in \
        data
    assert response.status_code == 200
    assert Participant.query.count() == 2


@mock.patch.dict("quizApp.views.mturk.session", values={
    "mturk_post_url": "foobar", "mturk_assignmentId": "barbaz",
    "mturk_hitId": "qux"})
def test_submit_assignment(app):
    with app.app_context():
        form = mturk.submit_assignment()
    assert "foobar" in form
    assert "barbaz" in form
