"""Tests for dataset views.
"""
import factory

from werkzeug.datastructures import FileStorage

from quizApp.forms.datasets import GraphForm
from tests.helpers import json_success
from tests.auth import login_experimenter
from tests.factories import DatasetFactory, GraphFactory, MediaItemFactory
from quizApp.models import Dataset
from quizApp import db
import mock


def test_read_datasets(client, users):
    login_experimenter(client)
    datasets = factory.create_batch(DatasetFactory, 10)
    db.session.add_all(datasets)
    db.session.commit()

    response = client.get("/datasets/")
    assert response.status_code == 200
    for dataset in datasets:
        assert dataset.name in response.data


def test_create_dataset(client, users):
    login_experimenter(client)

    assert Dataset.query.count() == 0

    dataset = DatasetFactory()

    response = client.post("/datasets/", data={"name": dataset.name,
                                               "uri": dataset.uri})

    assert response.status_code == 200
    assert json_success(response.data)

    assert Dataset.query.count() == 1
    created_dataset = Dataset.query.one()

    assert created_dataset.name == dataset.name
    assert created_dataset.uri == dataset.uri

    response = client.post("/datasets/")

    assert response.status_code == 200
    assert not json_success(response.data)

    response = client.get("/datasets/")
    assert response.status_code == 200
    assert dataset.name in response.data


def test_update_dataset(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.save()

    new_dataset = DatasetFactory()
    url = "/datasets/" + str(dataset.id)

    response = client.put(url, data={"name": new_dataset.name,
                          "uri": new_dataset.uri})
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get("/datasets/")
    assert response.status_code == 200
    assert new_dataset.name in response.data

    response = client.put(url)
    assert response.status_code == 200
    assert not json_success(response.data)


def test_delete_dataset(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.save()

    url = "/datasets/" + str(dataset.id)

    response = client.delete(url)
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get("/datasets/")
    assert response.status_code == 200
    assert dataset.name not in response.data


def test_create_media_item(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.save()
    initial_num_media_items = len(dataset.media_items)

    url = "/datasets/" + str(dataset.id)

    graph = GraphFactory()

    response = client.post(url + "/media_items/", data={"object_type":
                                                        graph.type})
    assert response.status_code == 200
    assert json_success(response.data)

    response = client.get(url + "/settings")
    assert response.status_code == 200
    assert graph.type in response.data

    db.session.refresh(dataset)

    assert len(dataset.media_items) == 1 + initial_num_media_items

    response = client.post(url + "/media_items/")
    assert response.status_code == 200
    assert not json_success(response.data)


def test_delete_dataset_media_item(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.save()
    initial_num_media_items = len(dataset.media_items)

    url = ("/datasets/" + str(dataset.id) + "/media_items/" +
           str(dataset.media_items[0].id))

    response = client.delete(url)
    assert response.status_code == 200
    assert json_success(response.data)

    db.session.refresh(dataset)

    assert len(dataset.media_items) == initial_num_media_items - 1

    unrelated_media_item = MediaItemFactory()
    unrelated_media_item.save()
    url = ("/datasets/" + str(dataset.id) + "/media_items/" +
           str(unrelated_media_item.id))

    response = client.delete(url)
    assert response.status_code == 404


def test_read_media_item(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.save()

    url = ("/datasets/" + str(dataset.id) + "/media_items/" +
           str(dataset.media_items[0].id))

    response = client.get(url)
    assert response.status_code == 200

    unrelated_media_item = MediaItemFactory()
    unrelated_media_item.save()
    url = ("/datasets/" + str(dataset.id) + "/media_items/" +
           str(unrelated_media_item.id))

    response = client.get(url)
    assert response.status_code == 404


def test_settings_media_item(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.media_items[0] = GraphFactory()
    dataset.save()
    graph = dataset.media_items[0]

    url = ("/datasets/" + str(dataset.id) + "/media_items/" + str(graph.id) +
           "/settings")

    response = client.get(url)
    assert response.status_code == 200
    assert graph.name in response.data

    unrelated_graph = GraphFactory()
    unrelated_graph.save()
    url = ("/datasets/" + str(dataset.id) + "/media_items/" +
           str(unrelated_graph.id) + "/settings")

    response = client.get(url)
    assert response.status_code == 404


def test_update_media_item(client, users):
    login_experimenter(client)
    dataset = DatasetFactory()
    dataset.media_items[0] = GraphFactory()
    dataset.save()
    graph = dataset.media_items[0]

    new_graph = GraphFactory()

    url = "/datasets/" + str(dataset.id) + "/media_items/" + str(graph.id)

    response = client.put(url, data={"name": new_graph.name})
    assert response.status_code == 200
    assert json_success(response.data)

    db.session.refresh(graph)

    assert graph.name == new_graph.name

    response = client.put(url, data={"name": "a"*10000})
    assert response.status_code == 200
    assert not json_success(response.data)

    unrelated_media_item = MediaItemFactory()
    unrelated_media_item.save()
    url = ("/datasets/" + str(dataset.id) + "/media_items/" +
           str(unrelated_media_item.id))

    response = client.put(url, data={"name": unrelated_media_item.name})
    assert response.status_code == 404

    # Test uploading a graph

    url = "/datasets/" + str(dataset.id) + "/media_items/" + str(graph.id)

    """
    graph_form = GraphForm()
    graph_mock.set_spec(graph_form.graph)
    attrs = {"data": ""}
    graph_mock.configure_mock(**attrs)
    """

    with mock.patch("quizApp.views.datasets.GraphForm") as GraphFormMock:
        graph_form_mock = mock.MagicMock(spec_set=GraphForm(),
                                         name="graph_form_mock")
        file_storage_mock = mock.MagicMock(spec_set=FileStorage())
        file_storage_mock.configure_mock(filename="foo.png")

        attrs = {"graph.data": file_storage_mock}
        graph_form_mock.configure_mock(**attrs)

        GraphFormMock.configure_mock(return_value=graph_form_mock)

        response = client.put(url,
                              data={"graph": open("tests/data/graph.png")})
        assert response.status_code == 200
        assert json_success(response.data)
        assert file_storage_mock.save.called_once()
        assert str(graph.id) in file_storage_mock.save.call_args[0][0]

        with mock.patch("quizApp.views.datasets.os.path.isfile",
                        autospec=True) as isfile_mock:
            isfile_mock.return_value = True
            db.session.refresh(graph)
            file_storage_mock.reset_mock()
            response = client.put(url,
                                  data={"graph": open("tests/data/graph.png")})
            assert response.status_code == 200
            assert json_success(response.data)
            assert file_storage_mock.save.called_once()
            assert str(graph.path) in file_storage_mock.save.call_args[0][0]
