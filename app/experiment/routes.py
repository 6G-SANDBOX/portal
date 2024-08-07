import os
from datetime import datetime
from typing import Dict, List
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from config import Config as UploaderConfig
from REST import DispatcherApi
from app import db
from app.experiment import bp
from app.models import Experiment, Execution, Action, NS
from app.experiment.forms import ExperimentForm, RunExperimentForm
from app.execution.routes import getLastExecution
from Helper import Config, Log


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    listUEs: List[str] = list(Config().UEs.keys())
    nss: List[str] = []
    nsIds: List[int] = []

    # Get User's VNFs

    for ns in current_user.userNSs():
        nss.append(ns.name)
        nsIds.append(ns.id)

    form = ExperimentForm()
    if form.validate_on_submit():
        testCases = request.form.getlist('testCases')
        if not testCases:
            flash(f'Please, select at least one Test Case', 'error')
            return redirect(url_for('main.create'))

        ues_selected = request.form.getlist('ues')

        Log.D(f'Create experiment form data - Name: {form.name.data}, Type: {form.type.data}'
              f', TestCases {testCases}, UEs: {ues_selected}, Slice: {request.form.get("slice", None)}')

        experiment: Experiment = Experiment(name=form.name.data, author=current_user, unattended=True,
                                            type=form.type.data, test_cases=testCases, ues=ues_selected)
        formSlice = request.form.get('slice', None)
        if formSlice is not None:
            experiment.slice = formSlice

        # Manage multiple VNF-Location selection
        count = int(request.form.get('nsCount', '0'))
        for i in range(count):
            ns_i = 'NS' + str(i + 1)
            ns = NS.query.get(request.form[ns_i])
            if ns:
                if i == 0:  # TODO: Remove experiment.NSD and use only network_services
                    experiment.NSD = ns.NSD
                experiment.network_services.append(ns)

        db.session.add(experiment)
        db.session.commit()
        Log.I(f'Added experiment {experiment.id}')

        action: Action = Action(timestamp=datetime.utcnow(), author=current_user,
                                message=f'<a href="/experiment/{experiment.id}">Created experiment: {form.name.data}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Created experiment')
        flash('Your experiment has been successfully created', 'info')
        return redirect(url_for('main.index'))

    return render_template('experiment/create.html', title='Home', form=form, testCaseList=Config().TestCases,
                           ueList=listUEs, sliceList=Config().Slices, nss=nss, nsIds=nsIds)


@bp.route('/<experimentId>/reload', methods=['GET', 'POST'])
@bp.route('/<experimentId>', methods=['GET', 'POST'])
@login_required
def experiment(experimentId: int):
    config = Config()
    exp: Experiment = Experiment.query.get(experimentId)
    formRun = RunExperimentForm()
    if formRun.validate_on_submit():
        runExperiment(config)
        return redirect(f"{request.url}/reload")

    if exp is None:
        Log.I(f'Experiment not found')
        flash(f'Experiment not found', 'error')
        return redirect(url_for('main.index'))

    else:
        if exp.user_id is current_user.id:

            # Get Experiment's executions
            executions: List[Experiment] = exp.experimentExecutions()
            if len(executions) == 0:
                flash(f'The experiment {exp.name} doesn\'t have any executions yet', 'info')
                return redirect(url_for('main.index'))
            else:
                return render_template('experiment/experiment.html', title='experiment', experiment=exp,
                                       executions=executions, formRun=formRun, grafanaUrl=config.GrafanaUrl,
                                       executionId=getLastExecution() + 1)
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to access experiment {experimentId}')
            flash(f'Forbidden - You don\'t have permission to access this experiment', 'error')
            return redirect(url_for('main.index'))


@bp.route('/<experimentId>/nsdFile', methods=['GET'])
def downloadNSD(experimentId: int):
    experiment = Experiment.query.get(experimentId)
    if experiment is None: return render_template('errors/404.html'), 404

    # TODO: Handle experiments with multiple network services
    ns = experiment.network_services[0] if len(experiment.network_services) != 0 else None
    if ns is None: return render_template('errors/404.html'), 404
    filename = ns.NSD

    baseFolder = os.path.realpath(os.path.join(UploaderConfig.UPLOAD_FOLDER, 'nss', str(ns.id), 'nsd'))
    return send_from_directory(directory=baseFolder, filename=filename, as_attachment=True)


def runExperiment(config: Config):
    try:
        api = DispatcherApi(config.Dispatcher.Host, config.Dispatcher.Port, "/api/v0")  # //api/v0
        jsonResponse: Dict = api.Post(request.form['id'])
        Log.I(f'Ran experiment response {jsonResponse}')
        Log.I(f'Ran experiment {request.form["id"]}')
        # flash(f'Success: {jsonResponse["Success"]} - Execution Id: '
        #       f'{jsonResponse["ExecutionId"]} - Message: {jsonResponse["Message"]}', 'info')
        execution: Execution = Execution(id=jsonResponse["ExecutionId"], experiment_id=request.form['id'],
                                         status='Init')
        db.session.add(execution)
        db.session.commit()

        Log.I(f'Added execution {jsonResponse["ExecutionId"]}')
        exp: Experiment = Experiment.query.get(execution.experiment_id)
        action = Action(timestamp=datetime.utcnow(), author=current_user,
                        message=f'<a href="/execution/{execution.id}">Ran experiment: {exp.name}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Ran experiment')

    except Exception as e:
        Log.E(f'Error running expermient: {e}')
        flash(f'Exception while trying to connect with dispatcher: {e}', 'error')
