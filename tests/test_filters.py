"""Tests for filters.py.
"""

from tests.factories import GraphFactory
from quizApp.filters import get_graph_url_filter

def test_get_graph_url_filter(app):
    graph = GraphFactory()

    with app.test_request_context('/'):
        url = get_graph_url_filter(graph)

    assert "missing" in url


