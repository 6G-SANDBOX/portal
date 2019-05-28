from flask import request
from datetime import datetime
from app import db
from app.api import bp
from app.models import Execution
import json


@bp.route('/execution/<execution_id>', methods=['PATCH'])
def set_execution_status(execution_id):
    data = json.loads(request.data.decode('utf8'))
    execution = Execution.query.get(int(execution_id))
    if execution:
        if 'Status' in data:
            if data["Status"] in ['PreRun']:
                execution.start_time = datetime.utcnow()
            elif data["Status"] in ['Finished', 'Cancelled', 'Errored']:
                execution.end_time = datetime.utcnow()
            execution.status = data["Status"]
            print('Status of Execution ' + str(execution.id) + ' changed to ' + execution.status)
        if 'Dashboard' in data:
            execution.dashboard_url = str(data["Dashboard"])
        if 'PerCent' in data:
            execution.percent = data["PerCent"]
            print('PerCent ' + str(execution.percent))
        if 'Message' in data:
            execution.message = str(data["Message"])
            print('Message ' + str(execution.message))
        db.session.commit()
    return ""
