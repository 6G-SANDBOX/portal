from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import  DataRequired


class ExperimentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Add Experiment')


class RunExperimentForm(FlaskForm):
    id = HiddenField("id")
    submit = SubmitField('Run Experiment')
