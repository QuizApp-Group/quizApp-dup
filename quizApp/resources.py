from flask_restful import fields, Resource
from flask import request
from quizApp import schemas
from quizApp import models, api

class CollectionResource(Resource):
    def __init__(self, schema, retrieval_function=None):
        self.schema = schema
        self.model = schema.Meta.model
        self.retrieval_function = retrieval_function

    def get(self, **kwargs):
        schema = self.schema()
        if self.retrieval_function:
            records = self.retrieval_function(**kwargs)
        else:
            records = self.model.query.all()
        return schema.dump(records, many=True)

    def post(self, **kwargs):
        schema = self.schema()
        new_record = schema.load(request.data)
        if schema.errors:
            return schema.errors
        new_record.data.save()
        return None, 200

class ItemResource(Resource):
    def __init__(self, schema, pk_name):
        self.schema = schema
        self.model = schema.Meta.model
        self.pk_name = pk_name

    def get(self, **kwargs):
        schema = self.schema()
        record_id = kwargs.get(self.pk_name)
        record = self.model.query.get(record_id)
        return schema.dump(record)

def create_resource_endpoints(url, pk_name, schema, endpoint,
                              retrieval_function=None):
    api.add_resource(CollectionResource, url,
                     resource_class_kwargs={
                         'schema': schema,
                         'retrieval_function': retrieval_function,
                     },
                     endpoint=endpoint + "_list",
                     )
    api.add_resource(ItemResource,
                     url + '<int:' + pk_name + '>',
                     resource_class_kwargs={
                         'schema': schema,
                         'pk_name': pk_name,
                     },
                     endpoint=endpoint)

create_resource_endpoints("/experiments/", "experiment_id",
                          schemas.ExperimentSchema, "experiment")

def participant_experiment_retrieve(experiment_id):
    return models.ParticipantExperiment.query.filter_by(experiment_id=experiment_id).all()

create_resource_endpoints("/experiments/<int:experiment_id>/participant_experiments/",
                          "participant_experiment_id",
                          schemas.ParticipantExperimentSchema,
                          "participant_experiment",
                          retrieval_function=participant_experiment_retrieve)

def assignment_retrieve(experiment_id, participant_experiment_id):
    return models.Assignment.query.\
        filter_by(participant_experiment_id=participant_experiment_id).all()

create_resource_endpoints(
    "/experiments/<int:experiment_id>/participant_experiments/<int:participant_experiment_id>/assignments/",
    "assignment_id",
    schemas.AssignmentSchema,
    "assignment",
    retrieval_function=assignment_retrieve)

create_resource_endpoints(
    "/activities/",
    "activity_id",
    schemas.ActivitySchema,
    "activity")


