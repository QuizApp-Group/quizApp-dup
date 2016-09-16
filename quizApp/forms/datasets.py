"""Forms for dataset views.
"""

import os
from wtforms import SubmitField, FileField
from wtforms_alchemy import ModelForm
from flask import current_app

from quizApp import db
from quizApp.forms.common import OrderFormMixin
from quizApp.models import Graph, Dataset, Text


class UploadedFileField(FileField):
    """This behaves just like FileField, however when ``populate_obj`` is
    called it will overwrite the file pointed to by ``obj.name`` with the
    uploaded file.

    ``obj.directory`` must return the directory where the file is to be saved,
    if ``getattr(obj, name)`` does not exist.
    """
    def populate_obj(self, obj, name):
        if not self.data:
            return

        path = getattr(obj, name)
        # Replace the current graph with this

        if not os.path.isfile(path):
            # Need to create a new file
            file_name = str(obj.id) +\
                os.path.splitext(self.data.filename)[1]
            path = os.path.join(obj.directory, file_name)
            setattr(obj, name, path)
            db.session.commit()
        self.data.save(path)


class DatasetForm(OrderFormMixin, ModelForm):
    """Form for creation or update of a dataset.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Dataset
        order = ('*', 'submit')

    submit = SubmitField("Save")


class GraphForm(OrderFormMixin, ModelForm):
    """Form for updating Graph objects.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Graph
        exclude = ['path']
        order = ('*', 'submit')

    path = UploadedFileField("Replace graph", render_kw={"accept": "image/*"})
    submit = SubmitField("Save")


class TextForm(OrderFormMixin, ModelForm):
    """Form for updating Text objects.
    """
    class Meta(object):
        """Specify model and field order.
        """
        model = Text
        order = ('*', 'submit')

    submit = SubmitField("Save")
