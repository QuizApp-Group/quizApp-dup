"""Tests to make sure that create_app works as specified.
"""
from quizApp import create_app


def test_override():
    """Verify that overrides work.
    """
    app = create_app("development")
    csrf_enabled = app.config["WTF_CSRF_ENABLED"]
    app = create_app("development",
                     overrides={"WTF_CSRF_ENABLED": not csrf_enabled})
    assert csrf_enabled != app.config["WTF_CSRF_ENABLED"]
