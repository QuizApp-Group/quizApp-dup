import pytest
import mock

from quizApp.views.common import ObjectCollectionView, ObjectView


@mock.patch('quizApp.views.common.abort', autospec=True)
def test_ocv_dispatch_request(abort, app):
    ocv = ObjectCollectionView()

    with app.test_request_context('/'):
        ocv.dispatch_request()
    abort.assert_called_once_with(400)

    with pytest.raises(NotImplementedError):
        ocv.resolve_kwargs()

    with pytest.raises(NotImplementedError):
        ocv.get_members()

    with pytest.raises(NotImplementedError):
        ocv.create_form()

    with pytest.raises(NotImplementedError):
        ocv.template()

    with pytest.raises(NotImplementedError):
        ocv.create_member(None)


@mock.patch('quizApp.views.common.abort', autospec=True)
def test_ov_dispatch_request(abort, app):
    ov = ObjectView()

    with app.test_request_context('/'):
        ov.dispatch_request()
    abort.assert_called_once_with(400)

    with pytest.raises(NotImplementedError):
        ov.resolve_kwargs()

    with pytest.raises(NotImplementedError):
        ov.update_form()

    with pytest.raises(NotImplementedError):
        ov.collection_url()
