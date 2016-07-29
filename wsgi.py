"""Run a production server. For use with gunicorn, e.g.
"""
from quizApp import create_app

application = create_app("production")
