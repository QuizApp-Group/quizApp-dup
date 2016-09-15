from flask_restful import fields, Resource
from flask import request
from quizApp import models, restful
import pdb

class CollectionResource(Resource):
    def __init__(self, model, retrieval_function=None):
        self.model = model
        self.retrieval_function = retrieval_function

    def polymorphic_dump(self, records):
        result = []
        for record in records:
            schema = record.__marshmallow__()
            result.append(schema.dump(record).data)
        return result

    def get(self, **kwargs):
        if self.retrieval_function:
            records = self.retrieval_function(**kwargs)
        else:
            records = self.model.query.all()
        return self.polymorphic_dump(records)

    def post(self, **kwargs):
        schema = self.schema()
        new_record = schema.load(request.data)
        if schema.errors:
            return schema.errors
        new_record.data.save()
        return None, 200

class ItemResource(Resource):
    def __init__(self, model, pk_name):
        self.model = model
        self.pk_name = pk_name

    def get(self, **kwargs):
        record_id = kwargs.get(self.pk_name)
        record = self.model.query.get(record_id)
        schema = record.__marshmallow__()
        return schema.dump(record)

class ExperimentCollectionResource(CollectionResource):
    def __init__(self):
        super(ExperimentCollectionResource,
              self).__init__(model=models.Experiment)

class ExperimentItemResource(ItemResource):
    def __init__(self):
        super(ExperimentItemResource,
              self).__init__(model=models.Experiment,
                             pk_name="experiment_id")

restful.add_resource(ExperimentCollectionResource,
                     '/experiments/')
restful.add_resource(ExperimentItemResource,
                     '/experiments/<int:experiment_id>',
                     )

class AssignmentSetCollectionResource(CollectionResource):
    def __init__(self):
        super(AssignmentSetCollectionResource,
              self).__init__(model=models.AssignmentSet)

class AssignmentSetItemResource(ItemResource):
    def __init__(self):
        super(AssignmentSetItemResource,
              self).__init__(model=models.AssignmentSet,
                             pk_name="assignment_set_id")

restful.add_resource(AssignmentSetCollectionResource,
                     '/experiments/<int:experiment_id>/assignment_sets/')
restful.add_resource(AssignmentSetItemResource,
                     '/experiments/<int:experiment_id>/assignment_sets/<int:assignment_set_id>',
                     )

class AssignmentCollectionResource(CollectionResource):
    def __init__(self):
        super(AssignmentCollectionResource,
              self).__init__(model=models.Assignment)

class AssignmentItemResource(ItemResource):
    def __init__(self):
        super(AssignmentItemResource,
              self).__init__(model=models.Assignment,
                             pk_name="assignment_id")

restful.add_resource(AssignmentCollectionResource,
                     '/experiments/<int:experiment_id>/assignment_sets/<int:assignment_set_id>/assignments/')
restful.add_resource(AssignmentItemResource,
                     '/experiments/<int:experiment_id>/assignment_sets/<int:assignment_set_id>/assignments/<int:assignment_id>')

class ActivityCollectionResource(CollectionResource):
    def __init__(self):
        super(ActivityCollectionResource,
              self).__init__(model=models.Activity)

class ActivityItemResource(ItemResource):
    def __init__(self):
        super(ActivityItemResource,
              self).__init__(model=models.Activity,
                             pk_name="activity_id")

restful.add_resource(ActivityCollectionResource,
                     '/activities/')
restful.add_resource(ActivityItemResource,
                     '/activities/<int:activity_id>')
