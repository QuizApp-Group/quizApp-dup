from flask_restful import fields, Resource
from flask import request
from quizApp import models, restful, db
import pdb

class CollectionResource(Resource):
    def __init__(self, model, retrieval_function=None):
        self.model = model

    def polymorphic_dump(self, records):
        result = []
        for record in records:
            schema = record.__marshmallow__()
            result.append(schema.dump(record).data)
        return result

    def resolve_kwargs(self, **kwargs):
        raise NotImplementedError

    def get_records(self, **kwargs):
        raise NotImplementedError

    def generate_record(self, **kwargs):
        raise NotImplementedError

    def get(self, **kwargs):
        resolved_kwargs = self.resolve_kwargs(**kwargs)
        records = self.get_records(**resolved_kwargs)
        return self.polymorphic_dump(records)

    def post(self, **kwargs):
        resolved_kwargs = self.resolve_kwargs(**kwargs)
        schema = self.model.__marshmallow__(session=db.session)
        new_record = self.generate_record(**resolved_kwargs)
        pdb.set_trace()
        if request.data:
            data = schema.load(request.data, instance=new_record)
            if data.errors:
                return data.errors
        new_record.save()
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
    def resolve_kwargs(self):
        return {}

    def get_records(self):
        return models.Experiment.query.all()

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
    def resolve_kwargs(self, experiment_id):
        return {"experiment": models.Experiment.query.get(experiment_id) }

    def get_records(self, experiment):
        return experiment.assignment_sets

    def generate_record(self, experiment):
        return models.AssignmentSet(experiment=experiment)

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
