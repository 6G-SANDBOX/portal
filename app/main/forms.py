from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, SelectField
from wtforms.validators import DataRequired


class ExperimentForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    type = SelectField(u'type', choices=[('Standard', 'Standard'), ('Custom', 'Custom')])
    submit = SubmitField('Add Experiment')


class RunExperimentForm(FlaskForm):
    submit = SubmitField('Run Experiment')
