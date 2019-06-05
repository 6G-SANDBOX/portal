import os
from datetime import datetime
from typing import Dict, List
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from config import Config as UploaderConfig
from REST import Dispatcher_Api
from app import db
from app.experiment import bp
from app.models import Experiment, Execution, Action, VNFLocation
from app.experiment.forms import ExperimentForm, RunExperimentForm
from app.execution.routes import getLastExecution
from Helper import Config, Log


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    list_UEs: List[str] = list(Config().UEs.keys())
    vnfs: List[str] = []
    vnfs_id: List[int] = []
    if current_user.user_VNFs():
        for vnf in current_user.user_VNFs():
            vnfs.append(vnf.name)
            vnfs_id.append(vnf.id)
    form = ExperimentForm()
    if form.validate_on_submit():
        test_cases_selected = request.form.getlist('test_cases')
        ues_selected = request.form.getlist('ues')
        if not test_cases_selected:
            flash(f'Please, select at least one Test Case', 'error')
            return redirect(url_for('main.create'))

        Log.D(f'Create experiment form data - Name: {form.name.data}, Type: {form.type.data}'
              f', TestCases {test_cases_selected}, UEs: {ues_selected}, Slice: {request.form.get("slice", None)}')

        experiment: Experiment = Experiment(name=form.name.data, author=current_user, unattended=True,
                                            type=form.type.data, test_cases=test_cases_selected, ues=ues_selected)
        form_slice = request.form.get('slice', None)
        if form_slice is not None:
            experiment.slice = form_slice

        db.session.add(experiment)
        db.session.commit()
        Log.I(f'Added experiment {experiment.id}')

        if 'vnf_count' in request.form:
            count = int(request.form['vnf_count'])
        else:
            count = 0
        for i in range(count):
            loc = 'location'+str(i+1)
            vnf = 'VNF'+str(i+1)
            vnf_loc: VNFLocation = VNFLocation(location=request.form[loc], VNF_id=request.form[vnf], experiment_id=experiment.id)
            Log.D(f'Selected VNF {request.form[vnf]} with location {request.form[loc]}')
            db.session.add(vnf_loc)
            db.session.commit()
            Log.I(f'Added VNF-Location {vnf_loc.id} to experiment {experiment.id}')

        baseFolder = os.path.join(UploaderConfig.UPLOAD_FOLDER, 'experiment', str(experiment.id))
        os.makedirs(os.path.join(baseFolder, "nsd"), mode=0o755, exist_ok=True)

        if 'fileNSD' in request.files:
            fileNSD = request.files['fileNSD']
            if fileNSD.filename != '':
                fileNSD_name = secure_filename(fileNSD.filename)
                fileNSD.save(os.path.join(baseFolder, "nsd", fileNSD_name))
                experiment.NSD = fileNSD_name
                db.session.add(experiment)
                db.session.commit()
                Log.I(f'Added NSD file {fileNSD_name} to experiment {experiment.id}')
        
        action: Action = Action(timestamp=datetime.utcnow(), author=current_user,
                        message=f'<a href="/experiment/{experiment.id}">Created experiment: {form.name.data}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Created experiment')
        flash('Your experiment has been successfully created', 'info')
        return redirect(url_for('main.index'))
    return render_template('experiment/create.html', title='Home', form=form, test_case_list=Config().TestCases,
                           ue_list=list_UEs, slice_list=Config().Slices, vnfs=vnfs, vnfs_id=vnfs_id)


@bp.route('/<experiment_id>/reload', methods=['GET', 'POST'])
@bp.route('/<experiment_id>', methods=['GET', 'POST'])
@login_required
def experiment(experiment_id: int):
    exp: Experiment = Experiment.query.get(experiment_id)
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
            executions: List[Experiment] = exp.experiment_executions()
            if executions.count() == 0:
                flash(f'The experiment {exp.name} doesn\'t have any executions yet', 'info')
                return redirect(url_for('main.index'))
            else:
                return render_template('experiment/experiment.html', title='experiment', experiment=exp,
                                       executions=executions, formRun=formRun, grafana_url=config.GrafanaUrl,
                                       executionId=getLastExecution()+1)
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to access experiment {experiment_id}')
            flash(f'Forbidden - You don\'t have permission to access this experiment', 'error')
            return redirect(url_for('main.index'))


def runExperiment(config: Config):
    try:
        api = Dispatcher_Api(config.Dispatcher.Host, config.Dispatcher.Port, "/api/v0")  # //api/v0
        jsonresponse: Dict = api.Post(request.form['id'])
        Log.D(f'Ran experiment response {jsonresponse}')
        Log.I(f'Ran experiment {request.form["id"]}')
        flash(f'Success: {jsonresponse["Success"]} - Execution Id: '
              f'{jsonresponse["ExecutionId"]} - Message: {jsonresponse["Message"]}', 'info')
        execution: Execution = Execution(id=jsonresponse["ExecutionId"], experiment_id=request.form['id'],
                              status='Init')
        db.session.add(execution)
        db.session.commit()
        Log.I(f'Added execution {jsonresponse["ExecutionId"]}')
        exp: Experiment = Experiment.query.get(execution.experiment_id)
        action = Action(timestamp=datetime.utcnow(), author=current_user,
                        message=f'<a href="/execution/{execution.id}">Ran experiment: {exp.name}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Ran experiment')
    except Exception as e:
        Log.E(f'Error running expermient: {e}')
        flash(f'Exception while trying to connect with dispatcher: {e}', 'error')
