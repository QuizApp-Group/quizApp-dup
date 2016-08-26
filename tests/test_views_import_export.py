import pytest

from quizApp.views import import_export
from quizApp import models


def test_header_to_field_name():
    result = import_export.header_to_field_name("", models.Activity)
    assert result is None

    header = "fake_tablename:foobar"

    with pytest.raises(ValueError):
        import_export.header_to_field_name(header, models.Activity)


def test_get_object_from_id():
    with pytest.raises(ValueError):
        import_export.get_object_from_id(models.Activity, 5, {})
