"""Common objects for the views.
"""
import pdb
from flask import render_template, jsonify, request, url_for
from flask.views import MethodView
from quizApp import db


class ObjectListView(MethodView):
    """Generic class for rendering a collection of objects.
    """
    @property
    def model(self):
        """The model this collection operates on.
        """
        raise NotImplementedError

    @property
    def create_form(self):
        """A form used for creating new models that this collection will
        operate on.
        """
        raise NotImplementedError

    @property
    def read_template(self):
        """A template to display which records are in this collection.
        """
        raise NotImplementedError

    def member_url(self, record):
        """This should return the URL of a member of this collection. It is
        used as the page to load after creation.
        """
        raise NotImplementedError

    def get(self):
        """Get a list of records of this type.
        """
        object_list = self.model.query.all()
        create_form = self.create_form()

        return render_template(self.read_template,
                               object_list=object_list,
                               create_form=create_form)

    def post(self):
        """Create a new record of this type.
        """
        create_form = self.create_form(request.form)

        if not create_form.validate():
            return jsonify({"success": 0, "errors": create_form.errors})

        record = self.model()
        create_form.populate_obj(record)
        record.save()

        return jsonify({"success": 1, "next_url": self.member_url(record)})

class ObjectView(MethodView):
    @property
    def model(self):
        """The model this collection operates on.
        """
        raise NotImplementedError

    @property
    def update_form(self):
        """A form used for updating models that this collection will
        operate on.
        """
        raise NotImplementedError

    def collection_url(self, **kwargs):
        """Return url that leads to the collection of such objects.
        """
        raise NotImplementedError

    def get_record(self, **kwargs):
        """Given a bunch of url parameters, get the model they specify,
        validating as necessary.
        """
        raise NotImplementedError

    def put(self, **kwargs):
        record = self.get_record(**kwargs)
        update_record_form = self.update_form(request.form)

        if not update_record_form.validate():
            return jsonify({"success": 0, "errors":
                            update_record_form.errors})

        update_record_form.populate_obj(record)
        db.session.commit()
        return jsonify({"success": 1})

    def delete(self, **kwargs):
        record = self.get_record(**kwargs)
        db.session.delete(record)
        db.session.commit()

        return jsonify({"success": 1,
                        "next_url": self.collection_url(**kwargs)})


