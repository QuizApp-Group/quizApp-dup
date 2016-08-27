"""Common scaffolding for all views.
"""

from flask import render_template, request, abort, jsonify
from flask.views import View

from quizApp.forms.common import DeleteObjectForm
from quizApp import db


class ObjectCollectionView(View):
    """View for rendering a collection of objects.

    To use, populate ``methods`` with the methods you want this view to respond
    to. Then override the abstract functions below to implement functionality
    for your case.
    """
    methods = None

    def dispatch_request(self, **kwargs):
        """If this method is supported, run its function. Otherwise abort 400.
        """
        if request.method in self.methods:
            new_kwargs = self.resolve_kwargs(**kwargs)
            return getattr(self, request.method.lower())(**new_kwargs)
        abort(400)

    def resolve_kwargs(self, **kwargs):
        """Given a list of kwargs passed in as url arguments, perform any
        necessary validation or checking, then return a dict. e.g.::

            resolve_kwargs({"experiment_id": 5}) == {"experiment": <Experiment
            object>}
        """
        raise NotImplementedError

    def get_members(self, **kwargs):
        """Get the listing of members for this view.
        """
        raise NotImplementedError

    @property
    def create_form(self):
        """Get a creation form for this view.
        """
        raise NotImplementedError

    @property
    def template(self):
        """Return the template for this activity.
        """
        raise NotImplementedError

    def create_member(self, create_form, **kwargs):
        """Given a populated create_form and any keyword arguments, create a
        new member of this collection,
        """
        raise NotImplementedError

    def get(self, **kwargs):
        """Return a listing of this collection's members.
        """
        members = self.get_members(**kwargs)
        create_form = self.create_form()
        confirm_delete_form = DeleteObjectForm()

        return render_template(
            self.template,
            members=members,
            create_form=create_form,
            confirm_delete_form=confirm_delete_form)

    def post(self, **kwargs):
        """Create a new member in this collection.
        """
        create_form = self.create_form()

        if not create_form.validate():
            return jsonify({"success": 0, "errors": create_form.errors})

        response_kwargs = self.create_member(create_form, **kwargs)
        success = {"success": 1}
        success.update(response_kwargs)

        return jsonify(success)


class ObjectView(View):
    """View for managing a single instance of a model.
    """
    methods = None
    get_mapping = {}
    object_key = None
    template = None

    def resolve_kwargs(self, **kwargs):
        """Given a list of kwargs passed in as url arguments, perform any
        necessary validation or checking, then return a dict. e.g.::

            resolve_kwargs({"experiment_id": 5}) == {"experiment": <Experiment
            object>}
        """
        raise NotImplementedError

    @property
    def update_form(self):
        """Get an update form for this view.
        """
        raise NotImplementedError

    def collection_url(self, **kwargs):
        """Return the URL of the collection containing this object.
        """
        raise NotImplementedError

    def dispatch_request(self, **kwargs):
        """If this method is supported, run its function. Otherwise abort 400.
        """
        if request.method in self.methods:
            new_kwargs = self.resolve_kwargs(**kwargs)
            return getattr(self, request.method.lower())(**new_kwargs)
        abort(400)

    def get(self, **kwargs):
        """Get this object.
        """
        if self.get_mapping:
            return self.get_mapping[kwargs[self.object_key]](**kwargs)

        return render_template(self.template,
                               **kwargs)

    def put(self, **kwargs):
        """Update this object.
        """
        update_form = self.update_form(**kwargs)

        if not update_form.validate():
            return jsonify({"success": 0, "errors": update_form.errors})

        update_form.populate_obj(kwargs[self.object_key])
        db.session.commit()

        return jsonify({"success": 1})

    def delete(self, **kwargs):
        """Delete this object.
        """
        obj = kwargs[self.object_key]
        db.session.delete(obj)
        db.session.commit()

        return jsonify({"success": 1,
                        "next_url": self.collection_url(**kwargs)})
