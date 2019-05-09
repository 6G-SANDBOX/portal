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
    experiments = current_user.user_experiments()
    formrun = RunExperimentForm()
    if formrun.validate_on_submit():
        try:
            config = Config()
            api = Dispatcher_Api(config.Dispatcher.Host, config.Dispatcher.Port, "/api/v0")  # //api/v0
            jsonresponse = api.Post(request.form['id'])
            flash(f'Success: {jsonresponse["Success"]} - Execution Id: '
                  f'{jsonresponse["ExecutionId"]} - Message: {jsonresponse["Message"]}', 'info')
            execution = Execution(id=jsonresponse["ExecutionId"], experiment_id=request.form['id'], status='Init')
            db.session.add(execution)
            db.session.commit()
        except Exception as e:
            flash(f'Exception while trying to connect with dispatcher: {e}', 'error')
        return redirect(url_for('main.index'))
    return render_template('index.html', title='Home', formRun=formrun, experiments=experiments)


@bp.route('/new_experiment', methods=['GET', 'POST'])
@login_required
def new_experiment():
    list_UEs = list(Config().UEs.keys())
    form = ExperimentForm()
    if form.validate_on_submit():
        test_cases_selected = request.form.getlist('test_cases')
        ues_selected = request.form.getlist('ues')
        if not test_cases_selected:
            flash(f'Please, select at least one Test Case', 'error')
            return redirect(url_for('main.new_experiment'))
        experiment = Experiment(name=form.name.data, author=current_user, unattended=True, type=form.type.data,
                                test_cases=test_cases_selected, ues=ues_selected)
        db.session.add(experiment)
        db.session.commit()
        flash('Your experiment has been successfully created', 'info')
        return redirect(url_for('main.index'))
    return render_template('new_experiment.html', title='Home', form=form,
                           test_case_list=Config().TestCases, ue_list=list_UEs)


@bp.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
@login_required
def experiment(experiment_id):
    exp = Experiment.query.get(experiment_id)
    if exp is None:
        return render_template('errors/404.html'), 404
    else:
        executions = exp.experiment_executions()
    return render_template('experiment.html', title='Experiment', experiment=exp, executions=executions)


@bp.route('/execution/<execution_id>', methods=['GET', 'POST'])
@login_required
def execution(execution_id):
    exe = Execution.query.get(execution_id)
    try:
        config = Config()
        api = Dispatcher_Api(config.Dispatcher.Host, config.Dispatcher.Port, "/experiment")
        jsonresponse = api.Get(execution_id)
        status = jsonresponse["Status"]

    except Exception as e:
        flash(f'Exception while trying to connect with dispatcher: {e}', 'error')
    return render_template('execution.html', title='Execution', execution=exe, log_status=status)
