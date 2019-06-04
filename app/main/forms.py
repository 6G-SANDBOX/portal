from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired


class ExperimentForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    type = SelectField('type', choices=[('Standard', 'Standard'), ('Custom', 'Custom')])
    submit = SubmitField('Add Experiment')


class RunExperimentForm(FlaskForm):
    submit = SubmitField('Run Experiment')
