"""Common jinja filters for quizapp.
"""
import os

from flask import Blueprint, current_app, url_for

filters = Blueprint("filters", __name__)


@filters.app_template_filter("is_nav_child")
def is_nav_child(child, parent):
    """Check if the route child is a child of the route parent.

    This method is a bit ad-hoc, but it works for highlighting navigation tabs
    well enough.
    """
    if child[:4] == "core":
        return False

    child_parts = child.split(".")
    parent_parts = parent.split(".")

    return child_parts[0] == parent_parts[0]


@filters.app_template_filter("datetime_format")
def datetime_format_filter(value, fmt="%Y-%m-%d %H:%M:%S"):
    """Format the value (a datetime) according to fmt with strftime.
    """
    return value.strftime(fmt)


@filters.app_template_filter("get_graph_url")
def get_graph_url_filter(graph):
    """Given a graph, return html to display it.
    """
    if os.path.isfile(graph.path):
        filename = graph.filename()
    else:
        filename = current_app.config.get("EXPERIMENTS_PLACEHOLDER_GRAPH")

    graph_path = url_for(
        'static',
        filename=os.path.join(current_app.config.get("GRAPH_DIRECTORY"),
                              filename))
    return graph_path
