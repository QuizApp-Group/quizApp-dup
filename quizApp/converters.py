"""This file contains a list of custom converters.

We use converters to abstract out a lot of input value checking in views that
take in a model ID.
"""

from werkzeug.routing import BaseConverter
from quizApp import models
from flask import abort


def model_converter_factory(x):
    """Given a model, return a class that works as a converter for that model.
    """
    class ModelConverter(BaseConverter):
        """This class is a converter for models - it handles validating that
        models exist as well.
        """
        model = x

        def to_python(self, value):
            record = self.model.query.get(value)

            if not record:
                abort(404)

            return record

        def to_url(self, value):
            return str(value.id)
    return ModelConverter

CONVERTERS = {
    "dataset": model_converter_factory(models.Dataset),
    "experiment": model_converter_factory(models.Experiment),
    "activity": model_converter_factory(models.Activity),
    "media_item": model_converter_factory(models.MediaItem),
    "question": model_converter_factory(models.Question),
    "choice": model_converter_factory(models.Choice),
    "assignment": model_converter_factory(models.Assignment),
}
