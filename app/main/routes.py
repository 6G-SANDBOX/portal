from flask import render_template, redirect, url_for
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, Experiment
from app.experiment.forms import RunExperimentForm
from app.experiment.routes import runExperiment
from Helper import Config


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    experiments = current_user.user_experiments()
    formRun = RunExperimentForm()
    config = Config()
    notices = config.Notices
    if formRun.validate_on_submit():
        runExperiment(config)
        return redirect(url_for('main.index'))
    actions = User.query.get(current_user.id).user_actions()
    return render_template('index.html', title='Home', formRun=formRun, experiments=experiments, notices=notices,
                           actions=actions)
