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
    """
    file_dir = ""

    def __init__(self, *args, **kwargs):
        # TODO: can we move this elsewhere
        self.file_dir = os.path.join(
            current_app.static_folder,
            current_app.config.get("GRAPH_DIRECTORY"))
        super(UploadedFileField, self).__init__(*args, **kwargs)

    def populate_obj(self, obj, name):
        if not self.data:
            return

        path = getattr(obj, name)
        # Replace the current graph with this

        if not os.path.isfile(path):
            # Need to create a new file
            file_name = str(obj.id) +\
                os.path.splitext(self.data.filename)[1]
            path = os.path.join(self.file_dir, file_name)
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
