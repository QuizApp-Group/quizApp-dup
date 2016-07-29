"""Forms for core views.
"""
from flask_wtf import Form
from wtforms import SubmitField, FileField
from wtforms.validators import DataRequired


class ImportDataForm(Form):
    """Provide a FileField for an xlsx upload.
    """

    data = FileField("Import data", validators=[DataRequired()],
                     render_kw={"accept": ".xlsx"})
    submit = SubmitField("Submit")
