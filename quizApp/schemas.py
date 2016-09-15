from quizApp import models
from quizApp import ma
from marshmallow_sqlalchemy import ModelSchema

class ExperimentSchema(ModelSchema):
    class Meta:
        model = models.Experiment

class AssignmentSetSchema(ModelSchema):
    class Meta:
        model = models.AssignmentSet

class ActivitySchema(ModelSchema):
    class Meta:
        model = models.Activity

class AssignmentSchema(ModelSchema):
    class Meta:
        model = models.Assignment

class DatasetSchema(ModelSchema):
    class Meta:
        model = models.Dataset

class ChoiceSchema(ModelSchema):
    class Meta:
        model = models.Choice

class MediaItemSchema(ModelSchema):
    class Meta:
        model = models.MediaItem
