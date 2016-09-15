from flask_restful import fields, Resource
from flask import request
from quizApp import models, restful, db
import pdb

class CollectionResource(Resource):
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
        # TODO: this is a bit shaky
        data = schema.load(request.args, instance=new_record)
        if data.errors:
            return data.errors
        new_record.save()
        return None, 200


class ItemResource(Resource):
    def resolve_kwargs(self, **kwargs):
        raise NotImplementedError

    def get_record(self, **kwargs):
        raise NotImplementedError

    def get(self, **kwargs):
        new_kwargs = self.resolve_kwargs(**kwargs)
        record = self.get_record(**new_kwargs)
        schema = record.__marshmallow__()
        return schema.dump(record)

    def delete(self, **kwargs):
        new_kwargs = self.resolve_kwargs(**kwargs)
        record = self.get_record(**new_kwargs)
        db.session.delete(record)
        return None, 200

class ExperimentCollectionResource(CollectionResource):
    model = models.Experiment

    def resolve_kwargs(self):
        return {}

    def get_records(self):
        return models.Experiment.query.all()

    def generate_record(self):
        return models.Experiment()


class ExperimentItemResource(ItemResource):
    model = models.Experiment
    def resolve_kwargs(self, experiment_id):
        return {"experiment": models.Experiment.query.get(experiment_id)}

    def get_record(self, experiment):
        return experiment


restful.add_resource(ExperimentCollectionResource,
                     '/experiments/')
restful.add_resource(ExperimentItemResource,
                     '/experiments/<int:experiment_id>',
                     )

class AssignmentSetCollectionResource(CollectionResource):
    model = models.AssignmentSet
    def resolve_kwargs(self, experiment_id):
        return {"experiment": models.Experiment.query.get(experiment_id) }

    def get_records(self, experiment):
        return experiment.assignment_sets

    def generate_record(self, experiment):
        return models.AssignmentSet(experiment=experiment)


class AssignmentSetItemResource(ItemResource):
    model = models.AssignmentSet

    def resolve_kwargs(self, experiment_id, assignment_set_id):
        return {"experiment": models.Experiment.query.get(experiment_id),
                "assignment_set": models.AssignmentSet.query.get(assignment_set_id)}

    def get_record(self, experiment, assignment_set):
        return assignment_set

restful.add_resource(AssignmentSetCollectionResource,
                     '/experiments/<int:experiment_id>/assignment_sets/')
restful.add_resource(AssignmentSetItemResource,
                     '/experiments/<int:experiment_id>/assignment_sets/<int:assignment_set_id>',
                     )

class AssignmentCollectionResource(CollectionResource):
    model = models.Assignment
    def resolve_kwargs(self, experiment_id, assignment_set_id):
        return {"experiment": models.Experiment.query.get(experiment_id),
                "assignment_set": models.AssignmentSet.query.get(assignment_set_id)}
    def get_records(self, experiment, assignment_set):
        return assignment_set.assignments


class AssignmentItemResource(ItemResource):
    model = models.Assignment

    def resolve_kwargs(self, experiment_id, assignment_set_id, assignment_id):
        return {"experiment": models.Experiment.query.get(experiment_id),
                "assignment_set":
                models.AssignmentSet.query.get(assignment_set_id),
                "assignment": models.Assignment.query.get(assignment_id),
                }

    def get_record(self, experiment, assignment_set, assignment):
        return assignment

restful.add_resource(AssignmentCollectionResource,
                     '/experiments/<int:experiment_id>/assignment_sets/<int:assignment_set_id>/assignments/')
restful.add_resource(AssignmentItemResource,
                     '/experiments/<int:experiment_id>/assignment_sets/<int:assignment_set_id>/assignments/<int:assignment_id>')

"""
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
"""
