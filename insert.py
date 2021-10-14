import time

from flask import Blueprint
from flask import current_app
from flask import request

insert_bp = Blueprint('insert', __name__)


@insert_bp.route('/run_state/', methods=['POST', 'GET'])
def insert_run_state():
    req_data = request.get_json()
    db = current_app.config['mongo_col']
    if 'session_id' and 'device_identifier' in req_data:
        obj = db.find_one({'session_id': req_data['session_id']})
        if obj is None:
            db.insert_one(req_data)
        else:
            db.replace_one({"_id": obj['_id']}, req_data)
        update_last_alive(req_data)
        current_app.config['socketio'].emit('device-data', req_data)
    else:
        current_app.logger.error("ERROR in request body")
    return 'OK'


def update_last_alive(process_data):
    device_identifier = process_data['device_identifier']
    db = current_app.config['mongo_col']

    data = {
        'unique_device_identifier': device_identifier,
        'last_alive': int(time.time()),
        'last_session_id': process_data['session_id'],
    }
    obj = db.find_one({'unique_device_identifier': device_identifier})
    if obj is None:
        db.insert_one(data)
    else:
        db.replace_one({"_id": obj['_id']}, data)
