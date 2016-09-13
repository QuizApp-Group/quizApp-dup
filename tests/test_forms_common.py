import pytest

from quizApp.forms import common as common_forms


def test_list_object_form():
    lov = common_forms.ListObjectForm()

    with pytest.raises(NotImplementedError):
        lov.get_choice_tuple(None)
