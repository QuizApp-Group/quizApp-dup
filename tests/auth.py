"""Functions for handling logging in and out for testing purposes.
"""

from quizApp.models import User
from tests import conftest


def login_participant(client):
    """Log into the application with the specified username and password.
    """
    participant = User.query.filter_by(email=conftest.PARTICIPANT_EMAIL).one()
    login_user(client, participant)


def login_experimenter(client):
    """Log into the application as an experimenter.
    """
    experimenter = User.query.filter_by(
        email=conftest.EXPERIMENTER_EMAIL).one()
    login_user(client, experimenter)


def login_user(client, user):
    """Log in the given User in the given client.
    """
    response = client.post('/login', data=dict(
        email=user.email,
        password=user.password), follow_redirects=True)
    assert response.status_code == 200


def get_participant():
    """Return a participant model object.
    """

    return User.query.filter_by(email=conftest.PARTICIPANT_EMAIL).one()
