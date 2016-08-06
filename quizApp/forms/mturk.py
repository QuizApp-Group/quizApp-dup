"""Forms for the mturk views.
"""

from wtforms.fields import HiddenField, SubmitField
from wtforms import Form


class PostbackForm(Form):
    """Provide hidden fields necessary to send info back to amazon.
    """
    hitId = HiddenField("hitId")
    assignmentId = HiddenField("assignmentId")
    submit = SubmitField("Submit")
