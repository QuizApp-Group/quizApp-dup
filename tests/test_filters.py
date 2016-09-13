"""Tests for filters.py.
"""
import mock
import os

from tests.factories import GraphFactory
from quizApp.filters import get_graph_url_filter


@mock.patch("quizApp.filters.os.path.isfile", autospec=os.path.isfile)
def test_get_graph_url_filter(isfile_mock, app):
    isfile_mock.return_value = False
    graph = GraphFactory()

    with app.test_request_context('/'):
        url = get_graph_url_filter(graph)

    assert "missing" in url

    isfile_mock.return_value = True
    with app.test_request_context('/'):
        url = get_graph_url_filter(graph)

    assert "missing" not in url
