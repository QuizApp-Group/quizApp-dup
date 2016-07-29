"""Test the Experiments blueprint.
"""
import json
import random
import mock
from datetime import datetime, timedelta

from quizApp import db
from quizApp.models import ParticipantExperiment
from quizApp.views.experiments import get_participant_experiment_or_abort,\
    get_next_assignment_url, get_graph_url_filter
from tests.factories import ExperimentFactory, create_experiment, \
    GraphFactory, ParticipantFactory
from tests.auth import login_participant, get_participant, \
    login_experimenter
from tests.helpers import json_success


def test_experiments(client):
    """Make sure that the blueprint is inaccessible to users not logged in.
    """
    response = client.get("/experiments/")
    assert response.status_code == 302

    exp = ExperimentFactory()
    exp.save()

    response = client.get("/experiments/" + str(exp.id))
    assert response.status_code == 302

    response = client.delete("/experiments/" + str(exp.id))
    assert response.status_code == 302


def test_experiments_authed_participant(client, users):
    """Make sure logged in participants can see things.
    """
    login_participant(client)

    response = client.get("/")
    assert "Hello participant" in response.data

    participant = get_participant()
    exp = ExperimentFactory()
    exp.save()
    part_exp = ParticipantExperiment(experiment_id=exp.id,
                                     participant_id=participant.id)
    part_exp.save()

    exp_url = "/experiments/" + str(exp.id)

    response = client.get("/experiments/")
    assert response.status_code == 200
    assert exp.name in response.data

    response = client.get(exp_url)
    assert response.status_code == 200
    assert exp.name in response.data
    assert exp.blurb in response.data

    response = client.get(exp_url + "/settings")
    assert response.status_code == 302

    response = client.delete(exp_url)
    assert response.status_code == 302

    response = client.put(exp_url)
    assert response.status_code == 302


def test_experiments_authed_experimenter(client, users):
    """Make sure logged in experimenters can see things.
    """
    login_experimenter(client)

    response = client.get("/")
    assert "Hello experimenter" in response.data

    exp = ExperimentFactory()
    exp.save()

    exp_url = "/experiments/" + str(exp.id)

    response = client.get("/experiments/")
    assert response.status_code == 200
    assert exp.name in response.data

    response = client.get(exp_url)
    assert response.status_code == 200
    assert exp.name in response.data
    assert "Start" not in response.data

    response = client.get(exp_url + "/settings")
    assert response.status_code == 200

    response = client.put(exp_url)
    assert response.status_code == 200

    response = client.delete(exp_url)
    assert response.status_code == 200
    assert json_success(response.data)


def test_delete_experiment(client, users):
    """Make sure logged in experimenters can delete expeirments.
    """
    login_experimenter(client)

    exp = ExperimentFactory()
    exp.save()

    exp_url = "/experiments/" + str(exp.id)

    response = client.delete(exp_url)
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get("/experiments/")
    assert response.status_code == 200
    assert exp.name not in response.data


def test_create_experiment(client, users):
    """Make sure logged in experimenters can create expeirments.
    """
    login_experimenter(client)

    exp = ExperimentFactory()
    datetime_format = "%Y-%m-%d %H:%M:%S"

    response = client.post("/experiments/", data=dict(
        name=exp.name,
        start=exp.start.strftime(datetime_format),
        stop=exp.stop.strftime(datetime_format),
        blurb=exp.blurb))
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get("/experiments/")
    assert response.status_code == 200
    assert exp.name in response.data

    response = client.post("/experiments/", data=dict(
        start=exp.start.strftime(datetime_format),
        stop=exp.stop.strftime(datetime_format),
        blurb=exp.blurb))
    data = json.loads(response.data)
    assert data["success"] == 0
    assert data["errors"]

    response = client.post("/experiments/", data=dict(
        name=exp.name,
        start=exp.start.strftime(datetime_format),
        stop=exp.start.strftime(datetime_format),
        blurb=exp.blurb))
    data = json.loads(response.data)
    assert data["success"] == 0
    assert data["errors"]

    response = client.post("/experiments/", data=dict(
        name=exp.name,
        start=(datetime.now() - timedelta(days=5)).strftime(datetime_format),
        stop=(datetime.now() - timedelta(days=1)).strftime(datetime_format),
        blurb=exp.blurb))
    data = json.loads(response.data)
    assert data["success"] == 0
    assert data["errors"]


@mock.patch('quizApp.views.experiments.abort', autospec=True)
def test_get_participant_experiment_or_abort(abort_mock, client):
    """Make sure get_participant_experiment_or_abort actually aborts.
    """
    get_participant_experiment_or_abort(5, 500)

    abort_mock.assert_called_once_with(500)


def test_read_experiment(client, users):
    """Test the read_experiment method.
    """
    login_participant(client)

    participant = get_participant()

    exp = create_experiment(1, [participant])
    exp.save()

    url = "/experiments/" + str(exp.id)

    response = client.get(url)
    assert str(exp.participant_experiments[0].assignments[0].id) in \
        response.data

    exp.participant_experiments[0].assignments = []
    db.session.commit()


def test_update_experiment(client, users):
    login_experimenter(client)
    participant = get_participant()

    experiment = create_experiment(3, [participant])
    experiment.save()

    new_exp = ExperimentFactory()

    url = "/experiments/" + str(experiment.id)

    response = client.put(url,
                          data={})
    assert not json_success(response.data)

    datetime_format = "%Y-%m-%d %H:%M:%S"

    response = client.put(url,
                          data={
                              "name": new_exp.name,
                              "start":
                              experiment.start.strftime(datetime_format),
                              "stop": experiment.stop.strftime(datetime_format)
                          })
    assert json_success(response.data)

    response = client.get("/experiments/")

    assert new_exp.name in response.data


def test_read_assignment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, [participant],
                                   ["question_mc_singleselect"])
    participant_experiment = experiment.participant_experiments[0]
    participant_experiment.complete = False
    experiment.save()

    url = "/experiments/" + str(experiment.id) + "/assignments/"

    for assignment in participant_experiment.assignments:
        # Verify that the question is present in the output
        question = assignment.activity
        response = client.get(url + str(assignment.id))
        assert question.question in response.data

        # And save a random question
        choice = random.choice(assignment.activity.choices)
        response = client.patch(url + str(assignment.id),
                                data={"choices": str(choice.id)})

        assert response.status_code == 200
        assert json_success(response.data)

    response = client.patch("/experiments/" + str(experiment.id) + "/finalize")
    assert response.status_code == 200
    assert json_success(response.data)

    # Once an experiment is submitted, make sure defaults are saved and we have
    # next buttons
    for assignment in participant_experiment.assignments:
        response = client.get(url + str(assignment.id))
        assert response.status_code == 200
        assert "checked" in response.data
        assert "disabled" in response.data

    # Verify that we check that the assignment is in this experiment
    experiment2 = create_experiment(3, [participant])
    experiment2.save()
    participant_experiment2 = experiment2.participant_experiments[0]
    assignment2 = participant_experiment2.assignments[0]

    response = client.get(url + str(assignment2.id))
    assert response.status_code == 400

    # If we can't render it return an error
    url2 = "/experiments/" + str(experiment2.id) + "/assignments/"

    response = client.get(url2 + str(assignment2.id))
    assert response.status_code == 404
    experiment2 = create_experiment(3, [participant])

    # Make sure likert questions render correctly
    experiment3 = create_experiment(3, [participant],
                                    ["question_mc_singleselect_scale"])
    experiment3.save()
    participant_experiment3 = experiment3.participant_experiments[0]
    assignment3 = participant_experiment3.assignments[0]
    url3 = "/experiments/" + str(experiment3.id) + "/assignments/"

    response = client.get(url3 + str(assignment3.id))
    assert response.status_code == 200

    for choice in assignment3.activity.choices:
        assert choice.choice in response.data


def test_update_assignment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, [participant],
                                   ["question_mc_singleselect"])

    participant_experiment = experiment.participant_experiments[0]
    participant_experiment.complete = False
    participant_experiment.progress = 1
    experiment.save()

    assignment = participant_experiment.assignments[0]

    url = "/experiments/" + str(experiment.id) + "/assignments/" + \
        str(assignment.id)

    choice = random.choice(assignment.activity.choices)

    response = client.patch(url,
                            data={"choices": choice.id}
                            )

    assert response.status_code == 200
    assert json_success(response.data)

    # Make sure we can edit choices
    participant_experiment.progress = 0

    choice = random.choice(assignment.activity.choices)

    response = client.patch(url,
                            data={"choices": choice.id}
                            )

    assert response.status_code == 200
    assert json_success(response.data)

    response = client.patch(url)

    assert response.status_code == 200
    assert not json_success(response.data)

    # Test behavior for non-mc questions
    experiment2 = create_experiment(3, [participant])
    participant_experiment2 = experiment2.participant_experiments[0]
    participant_experiment2.complete = False
    experiment2.save()

    assignment2 = participant_experiment2.assignments[0]
    url = "/experiments/" + str(experiment2.id) + "/assignments/" + \
        str(assignment2.id)
    response = client.patch(url)

    assert response.status_code == 200
    assert json_success(response.data)

    # Make sure participants can't see each others' stuff
    other_participant = ParticipantFactory()
    experiment3 = create_experiment(3, [other_participant])
    participant_experiment3 = experiment3.participant_experiments[0]
    participant_experiment3.complete = False
    experiment3.save()

    assignment3 = participant_experiment3.assignments[0]
    url = "/experiments/" + str(experiment3.id) + "/assignments/" + \
        str(assignment3.id)
    response = client.patch(url)

    assert response.status_code == 403


def test_get_next_assignment_url(users):
    participant = get_participant()
    experiment = create_experiment(3, [participant])
    experiment.participant_experiments[0].complete = False
    experiment.save()

    url = get_next_assignment_url(experiment.participant_experiments[0],
                                  2)
    assert "done" in url


def test_finalize_experiment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, [participant],
                                   ["question_mc_singleselect"])
    experiment.save()

    url = "/experiments/" + str(experiment.id) + "/finalize"

    response = client.patch(url)
    assert response.status_code == 200
    assert json_success(response.data)

    url = "/experiments/" + str(experiment.id) + "/assignments/" + \
        str(experiment.participant_experiments[0].assignments[0].id)

    participant_experiment = experiment.participant_experiments[0]
    choice = random.choice(participant_experiment.assignments[0].
                           activity.choices)

    response = client.patch(url,
                            data={"choices": choice.id}
                            )

    assert response.status_code == 400


def test_get_graph_url_filter():
    graph = GraphFactory()

    url = get_graph_url_filter(graph)

    assert "missing" in url
