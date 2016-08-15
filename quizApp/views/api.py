"""Views for the API for quizapp.
"""

from flask import Blueprint, render_template, url_for, jsonify, abort, request
from flask_restful import Resource, fields, marshal_with
from quizApp import models, api

activity_resource_fields = {
    'type': fields.String,
    'category': fields.String,
    'experiments': fields.List(fields.String()),
}



class ActivityList(Resource):
    @marshal_with(activity_resource_fields, envelope='resource')
    def get(self):
        activities = models.Activity.query.all()

api.add_resource(ActivityList, "/activities/")
