"""Views for the Api for quizapp.
"""

from flask import Blueprint, render_template, url_for, jsonify, abort, request
from flask_restful import Resource, fields, marshal_with
from sqlalchemy.inspection import inspect
from quizApp.api import schemas
from quizApp import models, restful
from quizApp import ma, db
from sqlalchemy import exists
import pdb


class CollectionApi(Resource):
    """Operate on a collection of something.
    """
    class Meta(object):
        """Specify the model and schema classes for this collection.

        This should be overridden in child classes.
        """
        schema = None
        member_endpoint = None

    @property
    def model(self):
        """Return the model this class operates on, which is stored in the
        schema's Meta class.
        """
        return self.schema.Meta.model

    @property
    def schema(self):
        return self.Meta.member_endpoint.Meta.schema

    def get_member_url(self, record):
        """Given a record, return the API URL that can be used to update this
        record.

        """
        model = self.model
        record_id = getattr(record, inspect(model).primary_key[0].name)
        return restful.url_for(self.Meta.member_endpoint, record_id=record_id)

    def get(self):
        """Return a list of collections.
        """
        records = self.model.query.all()
        schema = self.schema()
        return schema.dump(records, many=True)

    def post(self):
        """Create a new item in this collection.
        """
        schema = self.schema()
        record = schema.load(request.args)
        if record.errors:
            return record.errors, 400
        return activities_schema.dump(record.data).data, 201, \
            {"Location": self.get_member_url(record)}


class ItemApi(Resource):
    """Operate on a specific item.
    """
    class Meta(object):
        """Specify the model and schema classes for this collection.

        This should be overridden in child classes.
        """
        model = None

    @property
    def model(self):
        """Return the model this class operates on, which is stored in the
        schema's Meta class.
        """
        return self.Meta.schema.Model

    def get(self, record_id):
        """Get the specified record.

        If no record is found, it will return 404.
        """
        record = self.model.query.get(record_id)
        if not record:
            return None, 404
        schema = self.Meta.schema()
        return schema.dump(record)

    def put(self, record_id):
        """Replace the specified record.

        If no record is found, it will return 404.

        If there is an error updating the record, it will return 400 and the
        response body will contain information about the error.
        """
        record = self.model.query.get(record_id)
        if not record:
            return None, 404
        schema = self.Meta.schema()
        updated_record = schema.load(request.args, instance=record)
        if updated_record.errors:
            return record.errors, 400
        db.session.commit()
        return None

    def patch(self, record_id):
        """Patch the specified record.

        If no record is found, it will return 404.

        If there is an error updating the record, it will return 400 and the
        response body will contain information about the error.
        """
        activity = models.Activity.query.get(activity_id)
        if not activity:
            return None, 404
        schema = self.Meta.schema()
        updated_record = activities_schema.load(request.args,
                                                instance=record,
                                                partial=True)
        if updated_record.errors:
            return updated_record.errors, 400
        db.session.commit()
        return None


class ActivityCollectionApi(CollectionApi):
    """Operations on the collection of Activities.
    """
    class Meta(object):
        schema = schemas.ActivitySchema

    def get_member_url(self, record):
        return restful.url_for(ActivityApi, activity_id=record.data.id)


restful.add_resource(ActivityCollectionApi, "/activities/")

class ActivityApi(ItemApi):
    """operation on a single Activity.
    """
    class Meta(object):
        model = models.Activity
        schema = schemas.ActivitySchema

restful.add_resource(ActivityApi, "/activities/<int:record_id>")

class ParticipantExperimentCollectionApi(CollectionApi):
    """Operations on a collection of ParticipantExperiments.
    """
    class Meta(object):
        schema = schemas.ParticipantExperimentSchema

    def get_member_url(self, record):
        return restful.url_for(ParticipantExperimentApi, record_id=record.data.id)
