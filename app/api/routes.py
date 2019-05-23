from flask import request
from datetime import datetime
from app import db
from app.api import bp
from app.models import Execution
from Helper import Config
import json


@bp.route('/execution/<execution_id>', methods=['PATCH'])
def set_execution_status(execution_id):
    data = json.loads(request.data.decode('utf8'))
    execution = Execution.query.get(int(execution_id))
    if 'Status' in data:
        if data["Status"] in ['PreRun']:
            execution.start_time = datetime.utcnow()
        elif data["Status"] in ['Finished', 'Cancelled', 'Errored']:
            execution.end_time = datetime.utcnow()
        execution.status = data["Status"]
    if 'Dashboard' in data:
        execution.dashboard_url = str(data["Dashboard"])

    db.session.commit()
    print('Status of Execution ' + str(execution.id) + ' changed to ' + execution.status)
    return ""
