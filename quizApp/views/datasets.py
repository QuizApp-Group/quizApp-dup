"""Views for CRUD datasets.
"""
import os

from werkzeug.datastructures import CombinedMultiDict
from flask import Blueprint, render_template, url_for, jsonify, abort, \
    request, current_app
from flask_security import roles_required

from quizApp import db
from quizApp.forms.common import DeleteObjectForm, ObjectTypeForm
from quizApp.forms.datasets import DatasetForm, GraphForm, TextForm
from quizApp.models import Dataset, MediaItem
from quizApp.views.helpers import validate_model_id, validate_form_or_error
from quizApp.views.common import ObjectCollectionView

datasets = Blueprint("datasets", __name__, url_prefix="/datasets")

MEDIA_ITEM_TYPES = {
    "graph": "Graph",
    "text": "Text",
}
DATASET_ROUTE = "/<int:dataset_id>"
MEDIA_ITEMS_ROUTE = os.path.join(DATASET_ROUTE + "/media_items/")
MEDIA_ITEM_ROUTE = os.path.join(MEDIA_ITEMS_ROUTE + "<int:media_item_id>")


class DatasetCollectionView(ObjectCollectionView):
    """View for managing a collection of Datasets.
    """
    decorators = [roles_required("experimenter")]
    methods = ["GET", "POST"]
    resolve_kwargs = dict
    template = "datasets/read_datasets.html"

    def create_form(self):
        return DatasetForm(request.form)

    def get_members(self):
        return Dataset.query.all()

    def create_member(self, create_form):
        dataset = Dataset()
        create_form.populate_obj(dataset)
        dataset.save()
        return {"next_url": url_for("datasets.settings_dataset",
                                    dataset_id=dataset.id)}

datasets.add_url_rule("/",
                      view_func=DatasetCollectionView.as_view('datasets'))


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
                    "next_url": url_for('datasets.datasets')})


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

    create_media_item_form = ObjectTypeForm()
    create_media_item_form.populate_object_type(MEDIA_ITEM_TYPES)
    confirm_delete_media_item_form = DeleteObjectForm()

    return render_template(
        "datasets/settings_dataset.html",
        dataset=dataset,
        update_dataset_form=update_dataset_form,
        confirm_delete_media_item_form=confirm_delete_media_item_form,
        create_media_item_form=create_media_item_form)


class MediaItemCollectionView(ObjectCollectionView):
    """Manage a collection of MediaItems.
    """
    decorators = [roles_required("experimenter")]
    methods = ["POST"]
    get_members = None
    template = None

    def resolve_kwargs(self, dataset_id):
        dataset = validate_model_id(Dataset, dataset_id)
        return {"dataset": dataset}

    def create_form(self):
        create_media_item_form = ObjectTypeForm()
        create_media_item_form.populate_object_type(MEDIA_ITEM_TYPES)
        return create_media_item_form

    def create_member(self, create_form, dataset):
        media_item = MediaItem(type=create_form.object_type.data,
                               dataset=dataset)
        media_item.save()

        return {
            "next_url": url_for("datasets.settings_media_item",
                                dataset_id=dataset.id,
                                media_item_id=media_item.id),
        }

datasets.add_url_rule(MEDIA_ITEMS_ROUTE,
                      view_func=MediaItemCollectionView.as_view('media_items'))


@datasets.route(MEDIA_ITEM_ROUTE + "/settings", methods=["GET"])
@roles_required("experimenter")
def settings_media_item(dataset_id, media_item_id):
    """View the configuration of some media item.

    Ultimately this view dispatches to another view for the specific type
    of media item.
    """
    dataset = validate_model_id(Dataset, dataset_id)
    media_item = validate_model_id(MediaItem, media_item_id)
    create_media_item_form = ObjectTypeForm()
    create_media_item_form.populate_object_type(MEDIA_ITEM_TYPES)

    if media_item not in dataset.media_items:
        abort(404)

    template = "datasets/settings_media_item.html"

    update_form_class_mapping = {
        "graph": GraphForm,
        "text": TextForm,
    }

    update_form_cls = update_form_class_mapping[media_item.type]

    return render_template(
        template,
        update_media_item_form=update_form_cls(obj=media_item),
        dataset=dataset,
        create_media_item_form=create_media_item_form,
        media_item=media_item)


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

    update_function_mapping = {
        "graph": update_graph,
        "text": update_text,
    }

    return update_function_mapping[media_item.type](dataset, media_item)


def update_text(_, text):
    """Update a Text object.
    """
    update_text_form = TextForm(request.form, request.files)

    response = validate_form_or_error(update_text_form)

    if response:
        return response

    update_text_form.populate_obj(text)

    db.session.commit()

    return jsonify({"success": 1})


def update_graph(_, graph):
    """Update a graph.
    """
    update_graph_form = GraphForm(CombinedMultiDict((request.form,
                                                     request.files)))

    response = validate_form_or_error(update_graph_form)

    if response:
        return response

    update_graph_form.populate_obj(graph)

    if update_graph_form.graph.data:
        # Replace the current graph with this
        if os.path.isfile(graph.path):
            # Just overwrite this
            update_graph_form.graph.data.save(graph.path)
        else:
            # Need to create a new file
            graphs_dir = os.path.join(
                current_app.static_folder,
                current_app.config.get("GRAPH_DIRECTORY"))
            graph_filename = str(graph.id) + \
                os.path.splitext(update_graph_form.graph.data.filename)[1]
            new_graph_path = os.path.join(graphs_dir, graph_filename)
            update_graph_form.graph.data.save(new_graph_path)
            graph.path = new_graph_path

    db.session.commit()

    return jsonify({"success": 1})
