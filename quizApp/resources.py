"""This file specifies endpoints for the API.
"""

from flask_restful import Resource
from flask import request
from quizApp import models, restful, db
from quizApp.views.helpers import validate_model_id


def polymorphic_dump(records):
    """Dump a list of items, dumping each with the schema appropriate for it.
    """
    result = []
    for record in records:
        schema = record.__marshmallow__()
        result.append(schema.dump(record).data)
    return result


class CollectionResource(Resource):
    """Class to handle a collection of items.
    """
    model = None

    def resolve_kwargs(self, **kwargs):
        """Turn ids into objects, and validate as necessary.
        """
        raise NotImplementedError

    def get_records(self, **kwargs):
        """Return the list of records for this collection.
        """
        raise NotImplementedError

    def generate_record(self, **kwargs):
        """Create a new object in this collection.
        """
        raise NotImplementedError

    def get(self, **kwargs):
        """Get a list of members in this collection.
        """
        resolved_kwargs = self.resolve_kwargs(**kwargs)
        records = self.get_records(**resolved_kwargs)
        return polymorphic_dump(records)

    def post(self, **kwargs):
        """Create a new member of this collection.
        """
        resolved_kwargs = self.resolve_kwargs(**kwargs)
        schema = self.model.__marshmallow__(session=db.session)
        new_record = self.generate_record(**resolved_kwargs)
        data = schema.load(request.args, instance=new_record)
        if data.errors:
            return data.errors
        new_record.save()
        return schema.dump(new_record).data, 201


class ItemResource(Resource):
    """Handle requests to a particular resource rather than a collection.
    """
    def resolve_kwargs(self, **kwargs):
        """Convert ids into objects and validate as necessary.
        """
        raise NotImplementedError

    def get_record(self, **kwargs):
        """Return the database record this resource references.
        """
        raise NotImplementedError

    def get(self, **kwargs):
        """Return a dump of the record this resource references.
        """
        new_kwargs = self.resolve_kwargs(**kwargs)
        record = self.get_record(**new_kwargs)
        schema = record.__marshmallow__()
        return schema.dump(record)

    def delete(self, **kwargs):
        """Delete this record.
        """
        new_kwargs = self.resolve_kwargs(**kwargs)
        record = self.get_record(**new_kwargs)
        db.session.delete(record)
        db.session.commit()
        return None, 200

    def post(self, **kwargs):
        """Return a 409 response if this record exists.
        """
        new_kwargs = self.resolve_kwargs(**kwargs)
        self.get_record(**new_kwargs)
        return None, 409

    def patch(self, **kwargs):
        """Apply a delta to this object.
        """
        new_kwargs = self.resolve_kwargs(**kwargs)
        record = self.get_record(**new_kwargs)
        schema = record.__marshmallow__()
        data = schema.load(request.args, instance=record)
        if data.errors:
            return data.errors
        db.session.commit()
        return schema.dump(record)


class ExperimentCollectionResource(CollectionResource):
    """Handle experiment collections.
    """
    model = models.Experiment

    def resolve_kwargs(self):
        return {}

    def get_records(self):
        return models.Experiment.query.all()

    def generate_record(self):
        return models.Experiment()


class ExperimentItemResource(ItemResource):
    """Handle a specific experiment.
    """
    def resolve_kwargs(self, experiment_id):
        return {"experiment": validate_model_id(models.Experiment,
                                                experiment_id)}

    def get_record(self, experiment):
        return experiment


restful.add_resource(ExperimentCollectionResource, '/experiments/')
restful.add_resource(ExperimentItemResource,
                     '/experiments/<int:experiment_id>',
                     )


class AssignmentSetCollectionResource(CollectionResource):
    """Handle assignment set collections.
    """
    model = models.AssignmentSet

    def resolve_kwargs(self, experiment_id):
        return {
            "experiment": validate_model_id(models.Experiment, experiment_id)
        }

    def get_records(self, experiment):
        return experiment.assignment_sets

    def generate_record(self, experiment):
        return models.AssignmentSet(experiment=experiment)


class AssignmentSetItemResource(ItemResource):
    """Handle a particular assignment set.
    """
    def resolve_kwargs(self, experiment_id, assignment_set_id):
        experiment = validate_model_id(models.Experiment, experiment_id),
        assignment_set = validate_model_id(models.AssignmentSet,
                                           assignment_set_id)

        if assignment_set.experiment != experiment:
            return None, 404

        return {"experiment": experiment, "assignment_set": assignment_set}

    def get_record(self, assignment_set, **_):
        return assignment_set

restful.add_resource(AssignmentSetCollectionResource,
                     '/experiments/<int:experiment_id>/assignment_sets/')
restful.add_resource(AssignmentSetItemResource,
                     ('/experiments/<int:experiment_id>/assignment_sets/'
                      '<int:assignment_set_id>'),
                     )


class AssignmentCollectionResource(CollectionResource):
    """Handle assignment collections.
    """
    model = models.Assignment

    def generate_record(self, assignment_set, **_):
        return models.Assignment(assignment_sett=assignment_set)

    def resolve_kwargs(self, experiment_id, assignment_set_id):
        experiment = validate_model_id(models.Experiment, experiment_id),
        assignment_set = validate_model_id(models.AssignmentSet,
                                           assignment_set_id)

        if assignment_set.experiment != experiment:
            return None, 404

        return {"experiment": experiment, "assignment_set": assignment_set}

    def get_records(self, assignment_set, **_):
        return assignment_set.assignments


class AssignmentItemResource(ItemResource):
    """Handle an assignment resource.
    """
    def resolve_kwargs(self, experiment_id, assignment_set_id, assignment_id):
        experiment = validate_model_id(models.Experiment, experiment_id),
        assignment_set = validate_model_id(models.AssignmentSet,
                                           assignment_set_id)
        assignment = validate_model_id(models.Assignment, assignment_id)

        if assignment_set.experiment != experiment:
            return None, 404

        if assignment.assignment_set != assignment:
            return None, 404

        return {"experiment": experiment, "assignment_set": assignment_set,
                "assignment": assignment}

    def get_record(self, assignment, **_):
        return assignment

restful.add_resource(AssignmentCollectionResource,
                     ('/experiments/<int:experiment_id>/assignment_sets/'
                      '<int:assignment_set_id>/assignments/'))
restful.add_resource(AssignmentItemResource,
                     ('/experiments/<int:experiment_id>/assignment_sets/'
                      '<int:assignment_set_id>/assignments/'
                      '<int:assignment_id>'))


class ActivityCollectionResource(CollectionResource):
    """Handle activity collections.
    """
    model = models.Activity

    def resolve_kwargs(self):
        return {}

    def generate_record(self):
        return models.Activity()

    def get_records(self):
        return models.Activity.query.all()


class ActivityItemResource(ItemResource):
    """Handle activity resources.
    """
    def resolve_kwargs(self, activity_id):
        return {"activity":  validate_model_id(models.Activity, activity_id),
                }

    def get_record(self, activity):
        return activity

restful.add_resource(ActivityCollectionResource,
                     '/activities/')
restful.add_resource(ActivityItemResource,
                     '/activities/<int:activity_id>')
