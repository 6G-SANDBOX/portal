import json
from datetime import datetime
from typing import Dict
from flask import request, jsonify
from app import db
from app.api import bp
from app.models import Execution
from app.execution.routes import getLastExecution
from Helper import Log


@bp.route('/execution/<execution_id>', methods=['PATCH'])
def set_execution_status(execution_id: int) -> Dict[str, str]:
    data: Dict = json.loads(request.data.decode('utf8'))
    Log.D(f'ELCM execution data (Execution: {execution_id}): {data}')
    execution: Execution = Execution.query.get(int(execution_id))
    if execution:
        if 'Status' in data:
            if data["Status"] in ['PreRun']:
                execution.start_time = datetime.utcnow()
            elif data["Status"] in ['Finished', 'Cancelled', 'Errored']:
                execution.end_time = datetime.utcnow()
            execution.status = data["Status"]
            Log.I(f'Execution {str(execution.id)}: Status changed to {execution.status}')
        if 'Dashboard' in data:
            execution.dashboard_url = str(data["Dashboard"])
            Log.I(f'Execution {str(execution.id)}: Dasboard URL assigned: {execution.dashboard_url}')
        if 'PerCent' in data:
            execution.percent = data["PerCent"]
            Log.I(f'Execution {str(execution.id)}: Percent - {str(execution.percent)}%')
        if 'Message' in data:
            execution.message = str(data["Message"])
            Log.I(f'Execution {str(execution.id)}: Message - {str(execution.message)}')
        db.session.commit()
    return jsonify({'Status': 'Success'})


@bp.route('/<int:executionId>/json')
def execution_json(executionId: int) -> Dict[str, object]:
    execution: Execution = Execution.query.get(executionId)
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
def nextExecutionId() -> Dict[str, int]:
    Log.D(f'Next execution ID: {getLastExecution() + 1}')
    return jsonify({'NextId': getLastExecution() + 1})
