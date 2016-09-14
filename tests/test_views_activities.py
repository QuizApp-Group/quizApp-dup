"""Test activity views.
"""
from __future__ import unicode_literals
from builtins import str
import factory

from tests.auth import login_experimenter
from tests import factories
from tests.helpers import json_success
from quizApp.views.activities import render_scorecard
from quizApp import db
from quizApp.models import Question, Scorecard


def test_read_activities(client, users):
    login_experimenter(client)
    activities = factory.create_batch(factories.QuestionFactory, 10)
    activities = factory.create_batch(factories.ScorecardFactory, 10)
    db.session.add_all(activities)
    db.session.commit()

    response = client.get("/activities/")
    data = response.data.decode(response.charset)

    for activity in activities:
        assert activity.category in data
        assert str(activity.id) in data


def test_create_activity(client, users):
    login_experimenter(client)

    question = factories.SingleSelectQuestionFactory()

    response = client.post("/activities/")
    assert response.status_code == 200
    assert not json_success(response.data)

    response = client.post("/activities/",
                           data={"object_type": question.type})
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get("/activities/")
    data = response.data.decode(response.charset)

    assert question.type in data


def test_read_activity(client, users):
    login_experimenter(client)

    question = factories.SingleSelectQuestionFactory()
    question.save()

    url = "/activities/" + str(question.id)

    response = client.get(url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert question.question in data
    assert question.explanation in data

    for choice in question.choices:
        assert choice.choice in data


def test_settings_activity(client, users):
    login_experimenter(client)

    question = factories.SingleSelectQuestionFactory()
    question.save()

    url = "/activities/" + str(question.id) + "/settings"

    response = client.get(url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert question.question in data
    assert question.explanation in data

    for choice in question.choices:
        assert choice.choice in data

    question = factories.IntegerQuestionFactory()
    question.save()
    url = "/activities/" + str(question.id) + "/settings"
    response = client.get(url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert question.question in data
    assert question.explanation in data


def test_settings_scorecard(client, users):
    login_experimenter(client)

    scorecard = Scorecard()
    scorecard.save()

    url = "/activities/" + str(scorecard.id) + "/settings"

    response = client.get(url)
    assert response.status_code == 200


def test_render_scorecard(client, users):
    login_experimenter(client)
    scorecard = factories.ScorecardFactory()
    scorecard.needs_comment = True
    scorecard.save()

    url = "/activities/" + str(scorecard.id)
    response = client.get(url)
    data = response.data.decode(response.charset)
    assert scorecard.title in data
    assert scorecard.prompt in data

    # make sure include_in_scorecards is respected
    exp = factories.create_experiment(100, 1, ["question_mc_singleselect",
                                               "question_mc_multiselect",
                                               "scorecard",
                                               "question_mc_singleselect_scale"
                                               ])
    assignment_set = exp.assignment_sets[0]
    scorecard = factories.ScorecardFactory()
    exp.save()

    rendered_sc = render_scorecard(scorecard, False, assignment_set, None, 100)

    for assignment in assignment_set.assignments:
        assert not assignment.activity.include_in_scorecards or \
            str(assignment.id) in rendered_sc


def test_update_activity(client, users):
    login_experimenter(client)

    question = factories.SingleSelectQuestionFactory()
    question.save()

    url = "/activities/" + str(question.id)

    new_question = factories.SingleSelectQuestionFactory()

    response = client.put(url)
    data = response.data.decode(response.charset)
    assert response.status_code == 200
    assert not json_success(response.data)
    assert "errors" in data

    response = client.put(url,
                          data={"question": new_question.question,
                                "explanation": new_question.explanation,
                                "num_media_items":
                                new_question.num_media_items}
                          )
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get(url)
    data = response.data.decode(response.charset)
    assert new_question.question in data
    assert new_question.explanation in data


def test_update_question_datasets(client, users):
    login_experimenter(client)
    question = factories.QuestionFactory()
    datasets = factory.create_batch(factories.DatasetFactory, 10)

    question.save()
    db.session.add_all(datasets)
    question.datasets.extend(datasets[:5])
    db.session.commit()

    url = "/activities/" + str(question.id) + "/datasets/"

    dataset_to_add = datasets[9]
    dataset_to_remove = question.datasets[0]

    response = client.post(url,
                           data={"dataset_id": str(dataset_to_add.id)})
    assert response.status_code == 200
    assert json_success(response.data)
    db.session.refresh(question)
    assert dataset_to_add in question.datasets

    del_url = "/activities/" + str(question.id) + "/datasets/" + \
        str(dataset_to_remove.id)
    response = client.delete(del_url)
    db.session.refresh(question)
    assert response.status_code == 200
    assert json_success(response.data)
    assert dataset_to_remove not in question.datasets

    response = client.delete(del_url)
    db.session.refresh(question)
    assert response.status_code == 400
    assert dataset_to_remove not in question.datasets

    response = client.post(url,
                           data={"dataset_id": str(dataset_to_add.id)})
    assert response.status_code == 400

    response = client.post(url)
    assert response.status_code == 400


def test_delete_activity(client, users):
    login_experimenter(client)
    question = factories.QuestionFactory()

    question.save()

    url = "/activities/" + str(question.id)

    response = client.delete(url)
    assert response.status_code == 200
    assert json_success(response.data)
    assert Question.query.get(question.id) is None


def test_create_choice(client, users):
    login_experimenter(client)
    question = factories.QuestionFactory()

    question.save()
    initial_num_choices = len(question.choices)
    choice = factories.ChoiceFactory()

    url = "/activities/" + str(question.id) + "/choices/"

    response = client.post(url, data={"create-choice": choice.choice,
                                      "create-label": choice.label,
                                      "create-correct": choice.correct})
    assert response.status_code == 200
    assert json_success(response.data)

    updated_question = Question.query.get(question.id)
    assert initial_num_choices + 1 == len(updated_question.choices)
    assert choice.choice in [c.choice for c in updated_question.choices]


def test_update_choice(client, users):
    login_experimenter(client)
    question = factories.QuestionFactory()
    question.save()
    choice = factories.ChoiceFactory()

    url = ("/activities/" + str(question.id) + "/choices/" +
           str(question.choices[0].id))

    response = client.put(url, data={"update-choice": choice.choice,
                                     "update-label": choice.label,
                                     "update-correct":
                                     str(choice.correct).lower()})
    assert response.status_code == 200
    assert json_success(response.data)

    updated_question = Question.query.get(question.id)
    assert updated_question.choices[0].choice == choice.choice
    assert updated_question.choices[0].label == choice.label
    assert updated_question.choices[0].correct == choice.correct

    unrelated_choice = factories.ChoiceFactory()
    unrelated_choice.save()

    url = ("/activities/" + str(question.id) + "/choices/" +
           str(unrelated_choice.id))
    response = client.put(url, data={"update-choice": choice.choice,
                                     "update-label": choice.label,
                                     "update-correct":
                                     str(choice.correct).lower()})
    assert response.status_code == 404


def test_delete_choice(client, users):
    login_experimenter(client)
    question = factories.QuestionFactory()
    question.save()

    initial_num_choices = len(question.choices)

    url = ("/activities/" + str(question.id) + "/choices/" +
           str(question.choices[0].id))

    response = client.delete(url)
    assert response.status_code == 200
    assert json_success(response.data)

    db.session.refresh(question)

    assert initial_num_choices - 1 == len(question.choices)

    unrelated_choice = factories.ChoiceFactory()
    unrelated_choice.save()

    url = ("/activities/" + str(question.id) + "/choices/" +
           str(unrelated_choice.id))
    response = client.delete(url)
    assert response.status_code == 404
