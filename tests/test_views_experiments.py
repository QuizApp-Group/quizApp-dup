"""Test the Experiments blueprint.
"""
from __future__ import unicode_literals
from builtins import str
from collections import Counter
import json
import random
import mock
from datetime import datetime, timedelta
from mock import patch

import openpyxl

from quizApp import db
from quizApp.models import AssignmentSet, Activity
from quizApp.views.experiments import get_next_assignment_url, \
    POST_FINALIZE_HANDLERS, validate_assignment_set, populate_row_segment, \
    get_activity_column_index
from tests.factories import ExperimentFactory, create_experiment, \
    ParticipantFactory, create_result
from tests.auth import login_participant, get_participant, \
    login_experimenter
from tests.helpers import json_success


@patch('quizApp.views.experiments.abort', autospec=True)
def test_validate_assignment_set(abort_mock):
    exp = create_experiment(4, 1)
    assignment_set = exp.assignment_sets[0]
    assignment_set.experiment = None
    exp.save()
    assignment_set.save()

    abort_mock.reset_mock()
    validate_assignment_set(exp.id, assignment_set.id)

    abort_mock.assert_called()


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
    data = response.data.decode(response.charset)
    assert "Hello participant" in data

    participant = get_participant()
    exp = ExperimentFactory()
    exp.save()
    assignment_set = AssignmentSet(experiment_id=exp.id,
                                   participant_id=participant.id)
    assignment_set.save()

    exp_url = "/experiments/" + str(exp.id)

    response = client.get(exp_url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert exp.name in data
    assert exp.blurb in data

    response = client.get(exp_url + "/settings")
    assert response.status_code == 302

    response = client.delete(exp_url)
    assert response.status_code == 403

    response = client.put(exp_url)
    assert response.status_code == 403

    exp.stop = datetime.now() - timedelta(days=50)
    response = client.get(exp_url)
    assert response.status_code == 400


def test_experiments_authed_experimenter(client, users):
    """Make sure logged in experimenters can see things.
    """
    login_experimenter(client)

    response = client.get("/")
    data = response.data.decode(response.charset)
    assert "Hello experimenter" in data

    exp = ExperimentFactory()
    assignment_set = AssignmentSet()
    exp.assignment_sets.append(assignment_set)
    exp.save()

    exp_url = "/experiments/" + str(exp.id)

    response = client.get("/experiments/")
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert exp.name in data

    response = client.get(exp_url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert exp.name in data
    assert "Start" not in data

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
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert exp.name not in data


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
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert exp.name in data

    response = client.post("/experiments/", data=dict(
        start=exp.start.strftime(datetime_format),
        stop=exp.stop.strftime(datetime_format),
        blurb=exp.blurb))
    data = response.data.decode(response.charset)
    json_data = json.loads(data)
    assert json_data["success"] == 0
    assert json_data["errors"]

    response = client.post("/experiments/", data=dict(
        name=exp.name,
        start=exp.start.strftime(datetime_format),
        stop=exp.start.strftime(datetime_format),
        blurb=exp.blurb))
    data = response.data.decode(response.charset)
    json_data = json.loads(data)
    assert json_data["success"] == 0
    assert json_data["errors"]

    response = client.post("/experiments/", data=dict(
        name=exp.name,
        start=(datetime.now() - timedelta(days=5)).strftime(datetime_format),
        stop=(datetime.now() - timedelta(days=1)).strftime(datetime_format),
        blurb=exp.blurb))
    data = response.data.decode(response.charset)
    json_data = json.loads(data)
    assert json_data["success"] == 0
    assert json_data["errors"]


def test_read_experiment(client, users):
    """Test the read_experiment method.
    """
    login_participant(client)

    exp = create_experiment(4, 1)
    exp.assignment_sets[0].complete = False
    exp.assignment_sets[0].progress = 0
    exp.save()

    url = "/experiments/" + str(exp.id)

    response = client.get(url)
    data = response.data.decode(response.charset)
    assert "/assignments/" + \
        str(exp.assignment_sets[0].assignments[0].id) in \
        data

    exp.assignment_sets[0].progress += 1
    db.session.commit()

    response = client.get(url)
    data = response.data.decode(response.charset)
    assert "/assignments/" + \
        str(exp.assignment_sets[0].assignments[0].id) not in \
        data
    assert "/assignments/" + \
        str(exp.assignment_sets[0].assignments[1].id) in \
        data

    exp.assignment_sets[0].progress = len(exp.assignment_sets[0].assignments)
    response = client.get(url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert "/assignments/{}".format(exp.assignment_sets[0].assignments[0].id) \
        in data


def test_update_experiment(client, users):
    login_experimenter(client)
    experiment = create_experiment(3, 1)
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
    data = response.data.decode(response.charset)

    assert new_exp.name in data


def test_read_assignment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, 1,
                                   ["question_mc_singleselect"])
    assignment_set = experiment.assignment_sets[0]
    assignment_set.complete = False
    assignment_set.participant = participant
    experiment.save()

    url = "/experiments/{}/assignment_sets/{}/assignments/".\
        format(experiment.id, assignment_set.id)

    for assignment in assignment_set.assignments:
        # Verify that the question is present in the output
        question = assignment.activity
        response = client.get(url + str(assignment.id))
        data = response.data.decode(response.charset)
        assert question.question in data
        assert "Time elapsed" not in data

        # And save a random choice
        choice = random.choice(assignment.activity.choices)
        response = client.patch(url + str(assignment.id),
                                data={"choices": str(choice.id)})

        assert response.status_code == 200
        assert json_success(response.data)

    for assignment in assignment_set.assignments:
        # Make sure we can read it
        question = assignment.activity
        response = client.get(url + str(assignment.id))
        data = response.data.decode(response.charset)
        assert response.status_code == 200
        assert question.question in data

    experiment.stop = datetime.now() - timedelta(days=1)

    for assignment in assignment_set.assignments:
        # Make sure we can't read it
        question = assignment.activity
        response = client.get(url + str(assignment.id))
        assert response.status_code == 400

    experiment.stop = datetime.now() + timedelta(days=1)

    experiment.disable_previous = True
    db.session.commit()

    response = client.get(url + str(assignment_set.assignments[0].id))
    assert response.status_code == 400

    response = client.patch(
        url + str(assignment_set.assignments[0].id),
        data={"choices": str(assignment_set.assignments[0].
                             activity.choices[0].id)})
    assert response.status_code == 400

    response = client.patch("/experiments/{}/assignment_sets/{}/finalize".
                            format(experiment.id, assignment_set.id))
    assert response.status_code == 200
    assert json_success(response.data)

    # Once an experiment is submitted, make sure defaults are saved and we have
    # next buttons
    for assignment in assignment_set.assignments:
        response = client.get(url + str(assignment.id))
        data = response.data.decode(response.charset)
        assert response.status_code == 200
        assert "checked" in data
        assert "disabled" in data

    # Verify that we check that the assignment is in this experiment
    experiment2 = create_experiment(3, 1)
    experiment2.save()
    assignment_set2 = experiment2.assignment_sets[0]
    assignment2 = assignment_set2.assignments[0]

    response = client.get(url + str(assignment2.id))
    assert response.status_code == 404

    # Make sure likert questions render correctly
    experiment3 = create_experiment(3, 1,
                                    ["question_mc_singleselect_scale"])
    experiment3.save()
    assignment_set3 = experiment3.assignment_sets[0]
    assignment_set3.participant = participant
    assignment_set3.save()
    assignment3 = assignment_set3.assignments[0]
    url3 = "/experiments/{}/assignment_sets/{}/assignments/".\
        format(experiment3.id, assignment_set3.id)

    response = client.get(url3 + str(assignment3.id))
    assert response.status_code == 200

    for choice in assignment3.activity.choices:
        data = response.data.decode(response.charset)
        assert choice.choice in data

    # Check that non-mc assignments are rendered OK
    experiment3 = create_experiment(3, 1,
                                    ["question_integer"])
    experiment3.save()
    assignment_set3 = experiment3.assignment_sets[0]
    assignment_set3.participant = participant
    assignment_set3.save()
    assignment3 = assignment_set3.assignments[0]
    url3 = "/experiments/{}/assignment_sets/{}/assignments/".\
        format(experiment3.id, assignment_set3.id)

    response = client.get(url3 + str(assignment3.id))
    assert response.status_code == 200
    data = response.data.decode(response.charset)
    assert assignment3.activity.question in data


def test_read_scorecard(client, users):
    login_participant(client)
    participant = get_participant()
    experiment = create_experiment(10, 1,
                                   ["question_mc_singleselect", "scorecard"])
    experiment.assignment_sets[0].participant = participant
    experiment.assignment_sets[0].complete = False
    experiment.save()

    url = "/experiments/{}/assignment_sets/{}/assignments/".\
        format(experiment.id, experiment.assignment_sets[0].id)

    for i, assignment in enumerate(experiment.assignment_sets[0].assignments):
        ass_url = url + str(assignment.id)

        response = client.get(ass_url)
        data = response.data.decode(response.charset)
        assert response.status_code == 200

        if i > 0:
            assert "Previous" in data
        if i < 9:
            assert "Next" in data


def test_update_assignment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, 1,
                                   ["question_mc_singleselect"])

    assignment_set = experiment.assignment_sets[0]
    assignment_set.complete = False
    assignment_set.progress = 1
    assignment_set.participant = participant
    experiment.save()

    assignment = assignment_set.assignments[0]

    url = "/experiments/{}/assignment_sets/{}/assignments/{}".\
        format(experiment.id, assignment_set.id, assignment.id)

    choice = random.choice(assignment.activity.choices)

    time_to_submit = timedelta(hours=1)
    start_ts = datetime.now()
    render_ts = start_ts.isoformat()
    submit_ts = (start_ts + time_to_submit).isoformat()

    response = client.patch(url,
                            data={"choices": choice.id,
                                  "render_time": render_ts,
                                  "submit_time": submit_ts}
                            )

    db.session.refresh(assignment)

    assert response.status_code == 200
    assert assignment.time_to_submit == time_to_submit
    assert json_success(response.data)

    # Test bad response
    response = client.patch(url,
                            data={"choices": choice.id + 10}
                            )

    db.session.refresh(assignment)

    assert response.status_code == 200
    assert assignment.time_to_submit == time_to_submit
    assert not json_success(response.data)

    # Test scorecards
    assignment.activity.scorecard_settings.display_scorecard = True
    db.session.commit()
    response = client.patch(url,
                            data={"choices": choice.id,
                                  "render_time": render_ts,
                                  "submit_time": submit_ts}
                            )

    assert response.status_code == 200
    data = response.data.decode(response.charset)
    assert json_success(response.data)
    assert "scorecard" in json.loads(data)

    # Make sure we can edit choices
    assignment_set.progress = 0

    choice = random.choice(assignment.activity.choices)

    response = client.patch(url,
                            data={"choices": choice.id}
                            )

    assert response.status_code == 200
    assert json_success(response.data)

    # Don't let them update old experiments
    experiment.stop = datetime.now() - timedelta(days=1)
    response = client.patch(url,
                            data={"choices": choice.id}
                            )
    assert response.status_code == 400
    experiment.stop = datetime.now() + timedelta(days=1)

    # Make sure participants can't see each others' stuff
    experiment3 = create_experiment(3, 1)
    assignment_set3 = experiment3.assignment_sets[0]
    assignment_set3.complete = False
    experiment3.save()

    assignment3 = assignment_set3.assignments[0]
    url = "/experiments/{}/assignment_sets/{}/assignments/{}".\
        format(experiment3.id, assignment_set3.id, assignment3.id)
    response = client.patch(url)

    assert response.status_code == 403


def test_update_int_assignment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, 1,
                                   ["question_integer"])

    assignment_set = experiment.assignment_sets[0]
    assignment_set.complete = False
    assignment_set.progress = 0
    assignment_set.participant = participant
    experiment.save()

    assignment = assignment_set.assignments[0]

    url = "/experiments/{}/assignment_sets/{}/assignments/{}".\
        format(experiment.id, assignment_set.id, assignment.id)

    time_to_submit = timedelta(hours=1)
    start_ts = datetime.now()
    render_ts = start_ts.isoformat()
    submit_ts = (start_ts + time_to_submit).isoformat()

    response = client.patch(url,
                            data={"integer": 5,
                                  "render_time": render_ts,
                                  "submit_time": submit_ts}
                            )

    db.session.refresh(assignment)

    assert response.status_code == 200
    assert assignment.time_to_submit == time_to_submit
    assert assignment.result.integer == 5
    assert json_success(response.data)


def test_get_next_assignment_url(users):
    experiment = create_experiment(3, 1)
    experiment.assignment_sets[0].complete = False
    experiment.save()

    url = get_next_assignment_url(experiment.assignment_sets[0],
                                  2)
    assert "done" in url


def test_finalize_experiment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, 1,
                                   ["question_mc_singleselect"])
    experiment.save()
    assignment_set = experiment.assignment_sets[0]
    assignment_set.participant = participant
    assignment_set.complete = False
    assignment_set.save()

    url_template = "/experiments/{}/assignment_sets/{}/finalize"

    url = url_template.format(experiment.id, assignment_set.id)

    response = client.patch(url)
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.patch(url)
    assert response.status_code == 400

    url = "/experiments/{}/assignment_sets/{}/assignments/{}".\
        format(experiment.id, experiment.assignment_sets[0].id,
               experiment.assignment_sets[0].assignments[0].id)

    choice = random.choice(assignment_set.assignments[0].
                           activity.choices)

    response = client.patch(url,
                            data={"choices": choice.id}
                            )

    assert response.status_code == 400


def test_done_experiment_hook(client, users):
    login_participant(client)
    participant = get_participant()

    experiment2 = create_experiment(3, 1, ["question_mc_singleselect"])
    experiment2.save()
    assignment_set2 = experiment2.assignment_sets[0]
    assignment_set2.participant = participant
    assignment_set2.complete = False
    assignment_set2.save()

    mock_handler = mock.MagicMock()
    POST_FINALIZE_HANDLERS["test_handler"] = mock_handler

    url_template = "/experiments/{}/assignment_sets/{}/done"

    url = url_template.format(experiment2.id, assignment_set2.id)
    with client.session_transaction() as sess:
        sess["experiment_post_finalize_handler"] = "test_handler"
    response = client.get(url)
    assert response.status_code == 200

    with client.session_transaction() as sess:
        sess["experiment_post_finalize_handler"] = None

    mock_handler.assert_called_once()


def test_done_experiment(client, users):
    login_participant(client)
    participant = get_participant()

    experiment = create_experiment(3, 1, ["question_mc_singleselect"])
    experiment.save()
    assignment_set = experiment.assignment_sets[0]
    assignment_set.complete = False
    assignment_set.participant = participant
    assignment_set.save()

    url_template = "/experiments/{}/assignment_sets/{}/done"

    url = url_template.format(experiment.id, assignment_set.id)

    response = client.get(url)
    assert response.status_code == 200

    experiment2 = create_experiment(3, 1)
    experiment2.save()

    url = url_template.format(experiment2.id,
                              experiment2.assignment_sets[0].id)

    response = client.get(url)
    assert response.status_code == 403

    url = url_template.format(experiment.id + 4, assignment_set.id)

    response = client.get(url)
    assert response.status_code == 404


def test_confirm_done_experiment(client, users):
    login_participant(client)
    participant = get_participant()
    experiment = create_experiment(1, 1)
    experiment.assignment_sets[0].participant = participant
    experiment.save()

    url_template = "/experiments/{}/assignment_sets/{}/confirm_done"

    url = url_template.format(experiment.id, experiment.assignment_sets[0].id)

    response = client.get(url)
    assert response.status_code == 200

    url = url_template.format(experiment.id + 4,
                              experiment.assignment_sets[0].id)

    response = client.get(url)
    assert response.status_code == 404


def test_results_experiment(client, users):
    login_experimenter(client)

    exp = create_experiment(1, 1)
    exp.save()
    url = "/experiments/" + str(exp.id) + "/results"
    response = client.get(url)
    assert response.status_code == 200


def test_populate_row_segment():
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    row_index = int(random.randint(1, 100))
    initial_col = int(random.randint(1, 100))
    data = range(0, int(random.randint(1, 100)))

    populate_row_segment(sheet, row_index, initial_col, data)

    for col_offset, datum in enumerate(data):
        assert sheet.cell(row=row_index,
                          column=col_offset + initial_col).value == datum


def test_export_experiment_results(client, users):
    login_experimenter(client)

    exp = create_experiment(10, 10, ["question_mc_singleselect", "scorecard",
                                     "question_mc_singleselect_scale",
                                     "question_mc_multiselect"])
    common_participant = ParticipantFactory()
    for assignment_set in exp.assignment_sets:
        if random.random() > .5:
            if random.random() > .5:
                assignment_set.participant = common_participant
            else:
                assignment_set.participant = ParticipantFactory()

            for assignment in assignment_set.assignments:
                if random.random() > .5:
                    result = create_result(assignment.activity)
                    assignment.result = result

    exp.save()
    url = "/experiments/{}/results/export".format(exp.id)

    response = client.get(url)
    assert response.status_code == 200

    exp = ExperimentFactory()
    exp.save()

    url = "/experiments/{}/results/export".format(exp.id)
    response = client.get(url)
    assert response.status_code == 200


def test_get_activity_column_index():
    activity = mock.MagicMock(autospec=Activity)
    activity.id = 5
    activity.__str__.return_value = ""
    counter = Counter()
    mapping = {}
    headers = []

    get_activity_column_index(activity, mapping, counter, headers)

    assert mapping[activity.id][0] == 1  # 1-indexed due to openpyxl
    assert len(mapping[activity.id]) == 1
    assert counter[activity.id] == 1

    get_activity_column_index(activity, mapping, counter, headers)

    assert mapping[activity.id][0] == 1
    assert mapping[activity.id][1] == 4
    assert len(mapping[activity.id]) == 2
    assert counter[activity.id] == 2
