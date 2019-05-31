from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from REST import Dispatcher_Api
from app import db
from app.main import bp
from app.models import User, Experiment, Execution, Action, VNF, VNFLocation
from app.main.forms import ExperimentForm, RunExperimentForm, VNFForm
from Helper import Config, LogInfo, Log
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import shutil
from config import Config as UploaderConfig


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


@bp.route('/new_experiment', methods=['GET', 'POST'])
@login_required
def new_experiment():
    list_UEs = list(Config().UEs.keys())
    vnfs = []
    vnfs_id = []
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
            return redirect(url_for('main.new_experiment'))

        Log.D(f'Create experiment form data - Name: {form.name.data}, Type: {form.type.data}'
              f', TestCases {test_cases_selected}, UEs: {ues_selected}, Slice: {request.form.get("slice", None)}')

        experiment = Experiment(name=form.name.data, author=current_user, unattended=True, type=form.type.data,
                                test_cases=test_cases_selected, ues=ues_selected)
        form_slice=request.form.get('slice', None)
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
            loc='location'+str(i+1)
            vnf='VNF'+str(i+1)
            vnf_loc = VNFLocation(location=request.form[loc], VNF_id=request.form[vnf], experiment_id=experiment.id)
            Log.D(f'Selected VNF {request.form[vnf]} with location {request.form[loc]}')
            db.session.add(vnf_loc)
            db.session.commit()
            Log.I(f'Added VNF-Location {vnf_loc.id} to Experiment {experiment.id}')

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
                Log.I(f'Added NSD file {fileNSD_name} to Experiment {experiment.id}')
        
        action = Action(timestamp=datetime.utcnow(), author=current_user,
                        message=f'<a href="/experiment/{experiment.id}">Created experiment: {form.name.data}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Created experiment')
        flash('Your experiment has been successfully created', 'info')
        return redirect(url_for('main.index'))
    return render_template('new_experiment.html', title='Home', form=form, test_case_list=Config().TestCases,
                           ue_list=list_UEs, slice_list=Config().Slices, vnfs=vnfs, vnfs_id=vnfs_id)


@bp.route('/experiment/<experiment_id>/reload', methods=['GET', 'POST'])
@bp.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
@login_required
def experiment(experiment_id):
    exp = Experiment.query.get(experiment_id)
    formRun = RunExperimentForm()
    config = Config()
    if formRun.validate_on_submit():
        runExperiment(config)
        return redirect(f"{request.url}/reload")
    if exp is None:
        Log.I(f'Experiment not found')
        flash(f'Experiment not found', 'error')
        return redirect(url_for('main.index'))
    else:
        if exp.user_id is current_user.id:
            executions = exp.experiment_executions()
            if executions.count() == 0:
                flash(f'The experiment {exp.name} doesn\'t have any executions yet', 'info')
                return redirect(url_for('main.index'))
            else:
                return render_template('experiment.html', title='Experiment', experiment=exp, executions=executions,
                                       formRun=formRun, grafana_url=config.GrafanaUrl, executionId=getLastExecution()+1)
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to access experiment {experiment_id}')
            flash(f'Forbidden - You don\'t have permission to access this experiment', 'error')
            return redirect(url_for('main.index'))


@bp.route('/execution/<execution_id>/reloadLog', methods=['GET'])
@bp.route('/execution/<execution_id>', methods=['GET'])
@login_required
def execution(execution_id):
    exe = Execution.query.get(execution_id)
    if exe is None:
        Log.I(f'Execution not found')
        flash(f'Execution not found', 'error')
        return redirect(url_for('main.index'))
    else:
        exp = Experiment.query.get(exe.experiment_id)
        if exp.user_id is current_user.id:
            try:
                config = Config()
                api = Dispatcher_Api(config.Dispatcher.Host, config.Dispatcher.Port, "/experiment")
                jsonresponse = api.Get(execution_id)
                Log.D(f'Access exeuction logs response {jsonresponse}')
                status = jsonresponse["Status"]
                if status == 'Not Found':
                    Log.I(f'Execution not found')
                    flash(f'Execution not found', 'error')
                    return redirect(url_for('main.index'))
                else:
                    executor = LogInfo(jsonresponse["Executor"])
                    postRun = LogInfo(jsonresponse["PostRun"])
                    preRun = LogInfo(jsonresponse["PreRun"])
                    return render_template('execution.html', title='Execution', execution=exe, log_status=status,
                                           executor=executor, postRun=postRun, preRun=preRun, experiment=exp,
                                           grafana_url=config.GrafanaUrl, executionId=getLastExecution()+1)
            except Exception as e:
                Log.E(f'Error accessing execution{exe.experiment_id}: {e}')
                flash(f'Exception while trying to connect with dispatcher: {e}', 'error')
                return experiment(exe.experiment_id)
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to access execution{execution_id}')
            flash(f'Forbidden - You don\'t have permission to access this execution', 'error')
            return redirect(url_for('main.index'))


@bp.route('/vnf_repository', methods=['GET', 'POST'])
@login_required
def vnf_repository():
    VNFs = current_user.user_VNFs()
    return render_template('vnf_repository.html', title='Home', VNFs=VNFs)


@bp.route('/delete_VNF/<vnf_id>', methods=['GET'])
@login_required
def delete_VNF(vnf_id):
    vnf = VNF.query.get(vnf_id)
    if vnf:
        if vnf.user_id == current_user.id:
            db.session.delete(vnf)
            db.session.commit()
            shutil.rmtree(os.path.join(UploaderConfig.UPLOAD_FOLDER, 'vnfs', str(vnf_id)))
            Log.I(f'VNF {vnf_id} successfully removed')
            flash(f'The VNF has been successfully removed', 'info')
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to remove VNF {vnf_id}')
            flash(f'Forbidden - You don\'t have permission to remove this VNF', 'error')
    else:
        return render_template('errors/404.html'), 404
    return redirect(url_for('main.vnf_repository'))


@bp.route('/upload_VNF', methods=['GET', 'POST'])
@login_required
def upload_VNF():
    form = VNFForm()
    if form.validate_on_submit():
        if 'fileVNFD' not in request.files or 'fileImage' not in request.files:
            Log.I('Can\'t upload VNF. There are files missing')
            flash('There are files missing', 'error')
            return redirect(request.url)

        fileVNFD = request.files['fileVNFD']
        fileImage = request.files['fileImage']

        if fileVNFD.filename == '' or fileImage.filename == '':
            flash('There are files missing', 'error')
            return redirect(request.url)

        if fileVNFD and fileImage:
            fileVNFD_name = secure_filename(fileVNFD.filename)
            fileImage_name = secure_filename(fileImage.filename)

            Log.D(f'Upload VNF form data - Name: {form.name.data}, Description: {form.description.data}'
                  f', VNFD {fileVNFD_name}, image: {fileImage_name}')

            new_VNF = VNF(name=form.name.data, author=current_user, description=form.description.data,
                          VNFD=fileVNFD_name, image=fileImage_name)

            db.session.add(new_VNF)
            db.session.commit()
            Log.I(f'Added VNF {new_VNF.name}')
            action = Action(timestamp=datetime.utcnow(), author=current_user,
                            message=f'<a href="/vnf_repository">Uploaded VNF: {new_VNF.name}</a>')
            Log.I(f'Added action - Uploaded VNF')
            db.session.add(action)
            db.session.commit()

            baseFolder = os.path.join(UploaderConfig.UPLOAD_FOLDER, 'vnfs', str(new_VNF.id))
            os.makedirs(os.path.join(baseFolder, "vnfd"), mode=0o755, exist_ok=True)
            os.makedirs(os.path.join(baseFolder, "images"), mode=0o755, exist_ok=True)
            fileVNFD.save(os.path.join(baseFolder, "vnfd", fileVNFD_name))
            Log.D(f'Saved VNFD file {fileVNFD_name} in VNF {new_VNF.id}')
            fileImage.save(os.path.join(baseFolder, "images", fileImage_name))
            Log.D(f'Saved Image file {fileImage_name} in VNF {new_VNF.id}')

            flash('Your VNF has been successfully uploaded', 'info')
            return redirect(url_for('main.vnf_repository'))
        Log.I('Can\'t upload VNF. There are files missing')
        flash('There are files missing', 'error')
    return render_template('upload_VNF.html', title='Home', form=form)


def runExperiment(config):
    try:
        api = Dispatcher_Api(config.Dispatcher.Host, config.Dispatcher.Port, "/api/v0")  # //api/v0
        jsonresponse = api.Post(request.form['id'])
        Log.D(f'Ran Experiment response {jsonresponse}')
        Log.I(f'Ran Experiment {request.form["id"]}')
        flash(f'Success: {jsonresponse["Success"]} - Execution Id: '
              f'{jsonresponse["ExecutionId"]} - Message: {jsonresponse["Message"]}', 'info')
        execution = Execution(id=jsonresponse["ExecutionId"], experiment_id=request.form['id'],
                              status='Init')
        db.session.add(execution)
        db.session.commit()
        Log.I(f'Added execution {jsonresponse["ExecutionId"]}')
        exp = Experiment.query.get(execution.experiment_id)
        action = Action(timestamp=datetime.utcnow(), author=current_user,
                        message=f'<a href="/execution/{execution.id}">Ran experiment: {exp.name}</a>')
        db.session.add(action)
        db.session.commit()
        Log.I(f'Added action - Ran experiment')
    except Exception as e:
        Log.E(f'Error running expermient: {e}')
        flash(f'Exception while trying to connect with dispatcher: {e}', 'error')


@bp.route('/<int:executionId>/json')
def json(executionId: int):
    execution = Execution.query.get(executionId)
    percent = 0
    message = []
    if execution is not None:
        status = execution.status
        percent = execution.percent
        message = execution.message
    return jsonify({
        'Status': status, 'PerCent': percent, 'Message': message
    })


@bp.route('/nextExecutionId')
def nextExecutionId():
    Log.D(f'Next execution ID: {getLastExecution() + 1}')
    return jsonify({'NextId': getLastExecution() + 1})


def getLastExecution():
    return db.session.query(Execution).order_by(Execution.id.desc()).first().id
