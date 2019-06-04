from flask import render_template, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from REST import Dispatcher_Api
from app import db
from app.execution import bp
from app.models import Experiment, Execution
from Helper import Config, LogInfo, Log


@bp.route('/<execution_id>/reloadLog', methods=['GET'])
@bp.route('/<execution_id>', methods=['GET'])
@login_required
def execution(execution_id):
    exe = Execution.query.get(execution_id)
    if exe is None:
        Log.I(f'execution not found')
        flash(f'execution not found', 'error')
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
                    Log.I(f'execution not found')
                    flash(f'execution not found', 'error')
                    return redirect(url_for('main.index'))
                else:
                    executor = LogInfo(jsonresponse["Executor"])
                    postRun = LogInfo(jsonresponse["PostRun"])
                    preRun = LogInfo(jsonresponse["PreRun"])
                    return render_template('execution/execution.html', title='execution', execution=exe, log_status=status,
                                           executor=executor, postRun=postRun, preRun=preRun, experiment=exp,
                                           grafana_url=config.GrafanaUrl, executionId=getLastExecution()+1)
            except Exception as e:
                Log.E(f'Error accessing execution{exe.experiment_id}: {e}')
                flash(f'Exception while trying to connect with dispatcher: {e}', 'error')
                return Experiment.experiment(exe.experiment_id)
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to access execution{execution_id}')
            flash(f'Forbidden - You don\'t have permission to access this execution', 'error')
            return redirect(url_for('main.index'))


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
