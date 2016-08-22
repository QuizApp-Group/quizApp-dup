"""Common jinja filters for quizapp.
"""
import os

from flask import Blueprint, current_app, url_for, request

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


@filters.app_template_filter("prev_next_tabs")
def prev_next_tabs(tablist):
    """Given a list of tabs, return the previous and next tab.

    This is used for having "next" and "previous" buttons on pages.
    """
    prev_tab = None
    next_tab = None
    current_tab = None
    for ix, tab in enumerate(tablist):
        if tab[0] == request.endpoint:
            current_tab = ix
            break

    if current_tab is None:
        return None, None

    if current_tab > 0:
        prev_tab = tablist[current_tab - 1]

    try:
        next_tab = tablist[current_tab + 1]
    except IndexError:
        pass

    return prev_tab, next_tab
