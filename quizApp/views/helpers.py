"""Various functions that are useful in multiple views.
"""
from flask import abort, jsonify


def validate_model_id(model, model_id, code=404):
    """Given a model and id, retrieve and return that model from the database
    or abort with the given code.
    """
    obj = model.query.get(model_id)

    if not obj:
        abort(code)

    return obj


def validate_form_or_error(form):
    """Validate this form or return errors in JSON format.

    If the form is valid, None is returned.
    """
    if not form.validate():
        return jsonify({"success": 0, "errors": form.errors})

    return None
