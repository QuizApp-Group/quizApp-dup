"""Tests for view helpers.
"""

from mock import MagicMock, patch

from quizApp.models import Base
from quizApp.views.helpers import validate_model_id


@patch('quizApp.views.helpers.abort', autospec=True)
def test_validate_model_id(abort_mock):
    """Test the validate_model_id method.
    """
    obj_class_mock = MagicMock(spec_set=Base)
    attrs = {"query.get.return_value": None}
    obj_class_mock.configure_mock(**attrs)

    validate_model_id(obj_class_mock, 5)
    abort_mock.assert_called_once()
