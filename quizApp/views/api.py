"""Views for the API for quizapp.
"""

from flask import Blueprint, render_template, url_for, jsonify, abort, request
from flask_restful import Resource, fields, marshal_with
from quizApp import models, api

class MultiRelationshipField(fields.Raw):
    def format(self, value):
        return [x.id for x in value]


activity_resource_fields = {
    'id': fields.Integer,
    'type': fields.String,
    'category': fields.String,
    'experiments': MultiRelationshipField,
}


class ActivityList(Resource):
    """Operations on the collection of Activities.

    """
    @marshal_with(activity_resource_fields, envelope='activities')
    def get(self):
        activities = models.Activity.query.all()
        return activities

api.add_resource(ActivityList, "/activities/")
