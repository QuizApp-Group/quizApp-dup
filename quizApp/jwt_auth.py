"""Authentication methods for flask-jwt.
"""

from quizApp import security
from quizApp import jwt
from flask_security.utils import verify_password


@jwt.authentication_handler
def jwt_authenticate(username, password):
    """Authenticate a user.
    """
    user = security.datastore.find_user(email=username)
    if user and username == user.email and \
            verify_password(password, user.password) and \
            user.has_role("experimenter"):
        return user
    return None


@jwt.identity_handler
def jwt_load_user(payload):
    """Return a user record.
    """
    user = security.datastore.find_user(id=payload['identitity'])
    return user
