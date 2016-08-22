"""Views for CRUD datasets.
"""
import os

from werkzeug.datastructures import CombinedMultiDict
from flask import Blueprint, render_template, url_for, jsonify, abort, \
    request, current_app
from flask_security import roles_required

from quizApp import db
from quizApp.forms.common import DeleteObjectForm, ObjectTypeForm
from quizApp.forms.datasets import DatasetForm, GraphForm
from quizApp.models import Dataset, MediaItem
from quizApp.views.helpers import validate_form_or_error
from quizApp.views.common import ObjectListView, ObjectView

datasets = Blueprint("datasets", __name__, url_prefix="/datasets")

MEDIA_ITEM_TYPES = {
    "graph": "Graph",
}
DATASET_ROUTE = "/<dataset:dataset>"
MEDIA_ITEMS_ROUTE = os.path.join(DATASET_ROUTE + "/media_items/")
MEDIA_ITEM_ROUTE = os.path.join(MEDIA_ITEMS_ROUTE + "<media_item:media_item>")


class DatasetListView(ObjectListView):
    """Views for manipulating a collection of Datasets.
    """
    decorators = [roles_required("experimenter")]
    model = Dataset
    create_form = DatasetForm
    read_template = "datasets/read_datasets.html"

    def member_url(self, record):
        return url_for("datasets.dataset", dataset=record)


datasets.add_url_rule('/', view_func=DatasetListView.as_view("datasets"))


class DatasetView(ObjectView):
    """Views for manipulating a DataSet.
    """
    decorators = [roles_required("experimenter")]

    def update_form(self, record, form):
        return DatasetForm(form)

    model = Dataset

    def collection_url(self, **kwargs):
        return url_for("datasets.datasets")

    def get_record(self, dataset):
        return dataset


datasets.add_url_rule(DATASET_ROUTE, view_func=DatasetView.as_view("dataset"))


def update_graph(graph):
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


class MediaItemView(ObjectView):
    """Views for manipulating a MediaItem.
    """
    decorators = [roles_required("experimenter")]

    def collection_url(self, dataset, **kwargs):
        return url_for("datasets.settings_dataset", dataset=dataset)

    def get_record(self, dataset, media_item):
        if media_item not in dataset.media_items:
            abort(404)

        return media_item

    def get(self, dataset, media_item):
        """Get an html representation of a particular media_item.
        """
        self.get_record(dataset, media_item)

        return render_template("datasets/read_media_item.html",
                               media_item=media_item)

    def update_form(self, record, form):
        update_form_mapping = {
            "graph": GraphForm(CombinedMultiDict((request.form,
                                                  request.files))),
        }
        return update_form_mapping[record.type]

    put_mapping = {
        "graph": update_graph,
    }

datasets.add_url_rule(MEDIA_ITEM_ROUTE,
                      view_func=MediaItemView.as_view("media_item"))


@datasets.route(MEDIA_ITEMS_ROUTE, methods=["POST"])
@roles_required("experimenter")
def create_media_item(dataset):
    """Create a new media item.
    """
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


@datasets.route(DATASET_ROUTE + '/settings', methods=["GET"])
@roles_required("experimenter")
def settings_dataset(dataset):
    """View the configuration of a particular dataset.
    """
    update_dataset_form = DatasetForm(obj=dataset)

    delete_dataset_form = DeleteObjectForm()

    create_media_item_form = ObjectTypeForm()
    create_media_item_form.populate_object_type(MEDIA_ITEM_TYPES)

    return render_template("datasets/settings_dataset.html",
                           dataset=dataset,
                           update_dataset_form=update_dataset_form,
                           delete_dataset_form=delete_dataset_form,
                           create_media_item_form=create_media_item_form)


@datasets.route(MEDIA_ITEM_ROUTE + "/settings", methods=["GET"])
@roles_required("experimenter")
def settings_media_item(dataset, media_item):
    """View the configuration of some media item.

    Ultimately this view dispatches to another view for the specific type
    of media item.
    """
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
