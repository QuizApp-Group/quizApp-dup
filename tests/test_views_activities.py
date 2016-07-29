"""Test activity views.
"""
import factory

from tests.auth import login_experimenter
from tests.factories import ActivityFactory, SingleSelectQuestionFactory, \
    DatasetFactory, QuestionFactory, ChoiceFactory
from tests.helpers import json_success
from quizApp import db
from quizApp.models import Question


def test_read_activities(client, users):
    login_experimenter(client)
    activities = factory.create_batch(ActivityFactory, 10)
    db.session.add_all(activities)
    db.session.commit()

    response = client.get("/activities/")

    for activity in activities:
        assert activity.category in response.data
        assert str(activity.id) in response.data


def test_create_activity(client, users):
    login_experimenter(client)

    question = SingleSelectQuestionFactory()

    response = client.post("/activities/")
    assert response.status_code == 200
    assert not json_success(response.data)

    response = client.post("/activities/",
                           data={"object_type": question.type})
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get("/activities/")

    assert question.type in response.data


def test_read_activity(client, users):
    login_experimenter(client)

    question = SingleSelectQuestionFactory()
    question.save()

    url = "/activities/" + str(question.id)

    response = client.get(url)
    assert response.status_code == 200
    assert question.question in response.data
    assert question.explanation in response.data

    for choice in question.choices:
        assert choice.choice in response.data


def test_settings_activity(client, users):
    login_experimenter(client)

    question = SingleSelectQuestionFactory()
    question.save()

    url = "/activities/" + str(question.id) + "/settings"

    response = client.get(url)
    assert response.status_code == 200
    assert question.question in response.data
    assert question.explanation in response.data

    for choice in question.choices:
        assert choice.choice in response.data


def test_update_activity(client, users):
    login_experimenter(client)

    question = SingleSelectQuestionFactory()
    question.save()

    url = "/activities/" + str(question.id)

    new_question = SingleSelectQuestionFactory()

    response = client.put(url)
    assert response.status_code == 200
    assert not json_success(response.data)
    assert "errors" in response.data

    response = client.put(url,
                          data={"question": new_question.question,
                                "explanation": new_question.explanation,
                                "num_media_items":
                                new_question.num_media_items}
                          )
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get(url)
    assert new_question.question in response.data
    assert new_question.explanation in response.data


def test_update_question_datasets(client, users):
    login_experimenter(client)
    question = QuestionFactory()
    datasets = factory.create_batch(DatasetFactory, 10)

    question.save()
    db.session.add_all(datasets)
    db.session.commit()

    url = "/activities/" + str(question.id) + "/datasets"

    dataset_to_add = datasets[0]
    dataset_to_remove = question.datasets[0]

    response = client.patch(url,
                            data={"objects": [str(dataset_to_add.id),
                                              str(dataset_to_remove.id)]})
    assert response.status_code == 200
    assert json_success(response.data)

    updated_question = Question.query.get(question.id)
    assert dataset_to_add in updated_question.datasets
    assert dataset_to_remove not in updated_question.datasets

    response = client.patch(url)
    assert response.status_code == 200
    assert not json_success(response.data)


def test_delete_activity(client, users):
    login_experimenter(client)
    question = QuestionFactory()

    question.save()

    url = "/activities/" + str(question.id)

    response = client.delete(url)
    assert response.status_code == 200
    assert json_success(response.data)
    assert Question.query.get(question.id) is None


def test_create_choice(client, users):
    login_experimenter(client)
    question = QuestionFactory()

    question.save()
    initial_num_choices = len(question.choices)
    choice = ChoiceFactory()

    url = "/activities/" + str(question.id) + "/choices/"

    response = client.post(url, data={"create-choice": choice.choice,
                                      "create-label": choice.label,
                                      "create-correct": choice.correct})
    assert response.status_code == 200
    assert json_success(response.data)

    updated_question = Question.query.get(question.id)
    assert initial_num_choices + 1 == len(updated_question.choices)
    assert choice.choice in [c.choice for c in updated_question.choices]

    response = client.post(url)
    assert response.status_code == 200
    assert not json_success(response.data)


def test_update_choice(client, users):
    login_experimenter(client)
    question = QuestionFactory()
    question.save()
    choice = ChoiceFactory()

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

    response = client.put(url)
    assert response.status_code == 200
    assert not json_success(response.data)

    unrelated_choice = ChoiceFactory()
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
    question = QuestionFactory()
    question.save()

    initial_num_choices = len(question.choices)

    url = ("/activities/" + str(question.id) + "/choices/" +
           str(question.choices[0].id))

    response = client.delete(url)
    assert response.status_code == 200
    assert json_success(response.data)

    db.session.refresh(question)

    assert initial_num_choices - 1 == len(question.choices)

    unrelated_choice = ChoiceFactory()
    unrelated_choice.save()

    url = ("/activities/" + str(question.id) + "/choices/" +
           str(unrelated_choice.id))
    response = client.delete(url)
    assert response.status_code == 404
