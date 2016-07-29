"""Views for CRUD datasets.
"""
import os
from flask import Blueprint, render_template, url_for, jsonify, abort, request
from flask_security import roles_required

from quizApp.models import Dataset, MediaItem
from quizApp.forms.common import DeleteObjectForm, ObjectTypeForm
from quizApp.forms.datasets import DatasetForm, GraphForm
from quizApp import db
from quizApp.views.helpers import validate_model_id, validate_form_or_error

datasets = Blueprint("datasets", __name__, url_prefix="/datasets")

MEDIA_ITEM_TYPES = {
    "graph": "Graph",
}
DATASET_ROUTE = "/<int:dataset_id>"
MEDIA_ITEMS_ROUTE = os.path.join(DATASET_ROUTE + "/media_items/")
MEDIA_ITEM_ROUTE = os.path.join(MEDIA_ITEMS_ROUTE + "<int:media_item_id>")


@datasets.route("/", methods=["GET"])
@roles_required("experimenter")
def read_datasets():
    """Display a list of all datasets.
    """
    datasets_list = Dataset.query.all()
    create_dataset_form = DatasetForm()

    return render_template("datasets/read_datasets.html",
                           datasets=datasets_list,
                           create_dataset_form=create_dataset_form)


@datasets.route("/", methods=["POST"])
@roles_required("experimenter")
def create_dataset():
    """Create a new dataset.
    """
    create_dataset_form = DatasetForm(request.form)

    if not create_dataset_form.validate():
        return jsonify({"success": 0, "errors": create_dataset_form.errors})

    dataset = Dataset()
    create_dataset_form.populate_obj(dataset)

    dataset.save()

    return jsonify({"success": 1})


@datasets.route(DATASET_ROUTE, methods=["PUT"])
@roles_required("experimenter")
def update_dataset(dataset_id):
    """Change the properties of this dataset.
    """
    dataset = validate_model_id(Dataset, dataset_id)

    update_dataset_form = DatasetForm(request.form)

    if not update_dataset_form.validate():
        return jsonify({"success": 0, "errors": update_dataset_form.errors})

    update_dataset_form.populate_obj(dataset)

    db.session.commit()

    return jsonify({"success": 1})


@datasets.route(DATASET_ROUTE, methods=["DELETE"])
@roles_required("experimenter")
def delete_dataset(dataset_id):
    """Delete this dataset.
    """
    dataset = validate_model_id(Dataset, dataset_id)

    db.session.delete(dataset)
    db.session.commit()

    return jsonify({"success": 1,
                    "next_url": url_for('datasets.read_datasets')})


@datasets.route(MEDIA_ITEM_ROUTE, methods=["DELETE"])
@roles_required("experimenter")
def delete_dataset_media_item(dataset_id, media_item_id):
    """Delete a particular media_item in a particular dataset.
    """
    dataset = validate_model_id(Dataset, dataset_id)
    media_item = validate_model_id(MediaItem, media_item_id)

    if media_item not in dataset.media_items:
        abort(404)

    db.session.delete(media_item)
    db.session.commit()

    return jsonify({"success": 1})


@datasets.route(MEDIA_ITEM_ROUTE, methods=["GET"])
@roles_required("experimenter")
def read_media_item(dataset_id, media_item_id):
    """Get an html representation of a particular media_item.
    """
    dataset = validate_model_id(Dataset, dataset_id)
    media_item = validate_model_id(MediaItem, media_item_id)

    if media_item not in dataset.media_items:
        abort(404)

    return render_template("datasets/read_media_item.html",
                           media_item=media_item)


@datasets.route(DATASET_ROUTE + '/settings', methods=["GET"])
@roles_required("experimenter")
def settings_dataset(dataset_id):
    """View the configuration of a particular dataset.
    """
    dataset = validate_model_id(Dataset, dataset_id)

    update_dataset_form = DatasetForm(obj=dataset)

    delete_dataset_form = DeleteObjectForm()

    create_media_item_form = ObjectTypeForm()
    create_media_item_form.populate_object_type(MEDIA_ITEM_TYPES)

    return render_template("datasets/settings_dataset.html",
                           dataset=dataset,
                           update_dataset_form=update_dataset_form,
                           delete_dataset_form=delete_dataset_form,
                           create_media_item_form=create_media_item_form)


@datasets.route(MEDIA_ITEMS_ROUTE, methods=["POST"])
@roles_required("experimenter")
def create_media_item(dataset_id):
    """Create a new media item.
    """
    dataset = validate_model_id(Dataset, dataset_id)
    create_media_item_form = ObjectTypeForm()
    create_media_item_form.populate_object_type(MEDIA_ITEM_TYPES)

    response = validate_form_or_error(create_media_item_form)

    if response:
        return response

    media_item = MediaItem(type=create_media_item_form.object_type.data,
                           dataset=dataset)
    media_item.save()

    return jsonify({
        "success": 1,
    })


@datasets.route(MEDIA_ITEM_ROUTE + "/settings", methods=["GET"])
@roles_required("experimenter")
def settings_media_item(dataset_id, media_item_id):
    """View the configuration of some media item.

    Ultimately this view dispatches to another view for the specific type
    of media item.
    """
    dataset = validate_model_id(Dataset, dataset_id)
    media_item = validate_model_id(MediaItem, media_item_id)

    if media_item not in dataset.media_items:
        abort(404)

    if media_item.type == "graph":
        return settings_graph(dataset, media_item)


def settings_graph(dataset, graph):
    """Display settings for a graph.
    """
    update_graph_form = GraphForm(obj=graph)

    return render_template("datasets/settings_graph.html",
                           update_graph_form=update_graph_form,
                           dataset=dataset,
                           graph=graph)


@datasets.route(MEDIA_ITEM_ROUTE, methods=["PUT"])
@roles_required("experimenter")
def update_media_item(dataset_id, media_item_id):
    """Update a particular media item.

    Dispatches to a handler for the specific kind of media item.
    """
    dataset = validate_model_id(Dataset, dataset_id)
    media_item = validate_model_id(MediaItem, media_item_id)

    if media_item not in dataset.media_items:
        abort(404)

    if media_item.type == "graph":
        return update_graph(dataset, media_item)


def update_graph(_, graph):
    """Update a graph.
    """
    update_graph_form = GraphForm(request.form)

    response = validate_form_or_error(update_graph_form)

    if response:
        return response

    update_graph_form.populate_obj(graph)

    db.session.commit()
    return jsonify({"success": 1})
