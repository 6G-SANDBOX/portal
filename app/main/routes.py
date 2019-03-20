from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from REST import Dispatcher_Api
from app import db
from app.main import bp
from app.models import Experiment, Execution
from app.main.forms import ExperimentForm, RunExperimentForm
from Helper import Config


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = ExperimentForm()
    if form.validate_on_submit():
        test_cases_selected = request.form.getlist('test_cases')
        if not test_cases_selected:
            flash(f'Please, select at least one Test Case', 'error')
            return redirect(url_for('main.index'))
        experiment = Experiment(name=form.name.data, author=current_user, unattended=True, type=form.type.data, test_cases=test_cases_selected)
        db.session.add(experiment)
        db.session.commit()
        flash('Your experiment has been created', 'info')
        return redirect(url_for('main.index'))
    experiments = current_user.user_experiments()
    formrun = RunExperimentForm()
    if formrun.validate_on_submit():
        try:
            config = Config()
            api = Dispatcher_Api(config.Dispatcher.Host, config.Dispatcher.Port, "/api/v0")  # //api/v0
            jsonresponse = api.Post(formrun.id.data)
            flash(f'Success: {jsonresponse["Success"]} - Execution Id: '
                  f'{jsonresponse["ExecutionId"]} - Message: {jsonresponse["Message"]}', 'info')
            execution = Execution(id=jsonresponse["ExecutionId"], experiment_id=formrun.id.data, status='Init')
            db.session.add(execution)
            db.session.commit()
        except Exception as e:
            flash(f'Exception while trying to connect with dispatcher: {e}', 'error')

        return redirect(url_for('main.index'))
    return render_template('index.html', title='Home', form=form, formRun=formrun, experiments=experiments,
                           test_case_list=Config().TestCases)


@bp.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
@login_required
def experiment(experiment_id):
    exp = Experiment.query.get(experiment_id)
    if exp is None:
        return render_template('errors/404.html'), 404
    else:
        executions = exp.experiment_executions()
    return render_template('experiment.html', title='Experiment', experiment=exp, executions=executions)
