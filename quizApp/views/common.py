"""Common objects for the views.
"""
import pdb
from flask import render_template, jsonify, request
from flask.views import MethodView


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
