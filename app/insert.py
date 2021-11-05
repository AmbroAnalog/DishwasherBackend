import time
from datetime import datetime
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
        record_temperature_series(req_data)
    else:
        current_app.logger.error("ERROR in request body")
    return 'OK'


@insert_bp.route('/is_alive/',  methods=['POST', 'GET'])
def received_last_alive():
    req_data = request.get_json()
    if 'session_id' and 'device_identifier' in req_data:
        update_last_alive(req_data)
    return 'OK'


def record_temperature_series(process_data):
    db = current_app.config['mongo_col']
    temperature = process_data['machine_temperature']
    device_identifier = process_data['device_identifier']
    session_id = process_data['session_id']
    if process_data['program_time_start'] is None and process_data['program_time_end'] is not None:
        # abort record if program not started or already ended
        return

    temp_series = db.find_one({'unique_device_identifier': device_identifier, 'series_name': 'temperature_series'})
    if temp_series is not None and int(temp_series['session_id']) != int(session_id):
        # old program run => delete entry
        db.delete_one({'unique_device_identifier': device_identifier, 'series_name': 'temperature_series'})
        temp_series = None

    data_set = {
        'value': float(temperature),
        'time': datetime.now().isoformat()
    }
    if temp_series is None:
        data = {
            'series_name': 'temperature_series',
            'unique_device_identifier': device_identifier,
            'last_updated': int(time.time()),
            'session_id': int(session_id),
            'series': [ data_set ]
        }
        db.insert_one(data)
        current_app.config['socketio'].emit('temperature_series', data)
    elif (int(time.time()) - temp_series['last_updated']) > 60:
        db.find_one_and_update({'unique_device_identifier': device_identifier, 'series_name': 'temperature_series'},
                               {'$push': {'series': data_set}, '$set': {'last_updated': int(time.time())}})
        data = {}
        for key, value in temp_series.items():
            if key == '_id':
                data['document_id'] = str(value)
            else:
                data[key] = value
        current_app.config['socketio'].emit('temperature_series', data)


def update_last_alive(process_data):
    device_identifier = process_data['device_identifier']
    db = current_app.config['mongo_col']

    data = {
        'unique_device_identifier': device_identifier,
        'last_alive': int(time.time()),
        'last_session_id': process_data['session_id'],
        'series_name': 'device'
    }
    obj = db.find_one({'unique_device_identifier': device_identifier})
    if obj is None:
        _id = db.insert_one(data)
        obj_id = _id.inserted_id
    else:
        obj_id = obj['_id']
        db.replace_one({"_id": obj_id}, data)

    data['document_id'] = str(obj_id)
    current_app.config['socketio'].emit('is-alive', data)
