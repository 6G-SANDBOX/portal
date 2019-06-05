import os
from datetime import datetime
from typing import Dict, List
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from config import Config as UploaderConfig
from REST import DispatcherApi
from app import db
from app.experiment import bp
from app.models import Experiment, Execution, Action, VNFLocation
from app.experiment.forms import ExperimentForm, RunExperimentForm
from app.execution.routes import getLastExecution
from Helper import Config, Log


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    listUEs: List[str] = list(Config().UEs.keys())
    vnfs: List[str] = []
    vnfsId: List[int] = []
    if current_user.userVNFs():
        for vnf in current_user.userVNFs():
            vnfs.append(vnf.name)
            vnfsId.append(vnf.id)
    form = ExperimentForm()
    if form.validate_on_submit():
        testCases = request.form.getlist('testCases')
        ues_selected = request.form.getlist('ues')
        if not testCases:
            flash(f'Please, select at least one Test Case', 'error')
            return redirect(url_for('main.create'))

        Log.D(f'Create experiment form data - Name: {form.name.data}, Type: {form.type.data}'
              f', TestCases {testCases}, UEs: {ues_selected}, Slice: {request.form.get("slice", None)}')

        experiment: Experiment = Experiment(name=form.name.data, author=current_user, unattended=True,
                                            type=form.type.data, test_cases=testCases, ues=ues_selected)
        formSlice = request.form.get('slice', None)
        if formSlice is not None:
            experiment.slice = formSlice

        db.session.add(experiment)
        db.session.commit()
        Log.I(f'Added experiment {experiment.id}')

        if 'vnfCount' in request.form:
            count = int(request.form['vnfCount'])
        else:
            count = 0
        for i in range(count):
            loc = 'location'+str(i+1)
            vnf = 'VNF'+str(i+1)
            vnfLoc: VNFLocation = VNFLocation(location=request.form[loc], VNF_id=request.form[vnf], experiment_id=experiment.id)
            Log.D(f'Selected VNF {request.form[vnf]} with location {request.form[loc]}')
            db.session.add(vnfLoc)
            db.session.commit()
            Log.I(f'Added VNF-Location {vnfLoc.id} to experiment {experiment.id}')

        baseFolder = os.path.join(UploaderConfig.UPLOAD_FOLDER, 'experiment', str(experiment.id))
        os.makedirs(os.path.join(baseFolder, "nsd"), mode=0o755, exist_ok=True)

        if 'fileNSD' in request.files:
            fileNSD = request.files['fileNSD']
            if fileNSD.filename != '':
                fileNSDName = secure_filename(fileNSD.filename)
                fileNSD.save(os.path.join(baseFolder, "nsd", fileNSDName))
                experiment.NSD = fileNSDName
                db.session.add(experiment)
                db.session.commit()
                Log.I(f'Added NSD file {fileNSDName} to experiment {experiment.id}')
        
        action: Action = Action(timestamp=datetime.utcnow(), author=current_user,
                        message=f'<a href="/experiment/{experiment.id}">Created experiment: {form.name.data}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Created experiment')
        flash('Your experiment has been successfully created', 'info')
        return redirect(url_for('main.index'))
    return render_template('experiment/create.html', title='Home', form=form, testCaseList=Config().TestCases,
                           ueList=listUEs, sliceList=Config().Slices, vnfs=vnfs, vnfsId=vnfsId)


@bp.route('/<experimentId>/reload', methods=['GET', 'POST'])
@bp.route('/<experimentId>', methods=['GET', 'POST'])
@login_required
def experiment(experimentId: int):
    exp: Experiment = Experiment.query.get(experimentId)
    formRun = RunExperimentForm()
    config = Config()
    if formRun.validate_on_submit():
        runExperiment(config)
        return redirect(f"{request.url}/reload")
    if exp is None:
        Log.I(f'experiment not found')
        flash(f'experiment not found', 'error')
        return redirect(url_for('main.index'))
    else:
        if exp.user_id is current_user.id:
            executions: List[Experiment] = exp.experimentExecutions()
            if executions.count() == 0:
                flash(f'The experiment {exp.name} doesn\'t have any executions yet', 'info')
                return redirect(url_for('main.index'))
            else:
                return render_template('experiment/experiment.html', title='experiment', experiment=exp,
                                       executions=executions, formRun=formRun, grafanaUrl=config.GrafanaUrl,
                                       executionId=getLastExecution()+1)
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to access experiment {experimentId}')
            flash(f'Forbidden - You don\'t have permission to access this experiment', 'error')
            return redirect(url_for('main.index'))


def runExperiment(config: Config):
    try:
        api = DispatcherApi(config.Dispatcher.Host, config.Dispatcher.Port, "/api/v0")  # //api/v0
        jsonResponse: Dict = api.Post(request.form['id'])
        Log.D(f'Ran experiment response {jsonResponse}')
        Log.I(f'Ran experiment {request.form["id"]}')
        flash(f'Success: {jsonResponse["Success"]} - Execution Id: '
              f'{jsonResponse["ExecutionId"]} - Message: {jsonResponse["Message"]}', 'info')
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
