"""This file contains a list of custom converters.

We use converters to abstract out a lot of input value checking in views that
take in a model ID.
"""

from werkzeug.routing import BaseConverter
from quizApp import models

class ModelConverter(BaseConverter):
    def to_python(self, value):
        record = self.model.query.get(value)

        if not record:
            abort(404)

    def to_url(self, value):
        return str(value.id)


def model_converter_factory(model):


class ExperimentConverter(BaseConverter):
    def to_python(self, value):
        record = models.Experiment.query.get(value)

        if not record:
            abort(404)

    def to_url(self, value):
        return str(value.id)
