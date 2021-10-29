import time
import json

import pymongo
from bson.json_util import dumps
from bson import json_util
from bson.objectid import ObjectId
from bson.errors import InvalidId

from flask import Response
from flask import Blueprint
from flask import current_app
from flask import request
from flask_cors import CORS, cross_origin

request_bp = Blueprint('requests', __name__)


@request_bp.route('/get_all_devices/', methods=['GET'])
@cross_origin()
def request_device_list():
    db = current_app.config['mongo_col']

    devices = db.find({'unique_device_identifier': {'$exists': True}})

    device_list = []
    for device_obj in devices:
        device = {}
        for key, value in device_obj.items():
            if key == '_id':
                device['document_id'] = str(value)
            else:
                device[key] = value
        device_list.append(device)

    return json.dumps(device_list)

@request_bp.route('/get_all_runs/', methods=['GET'])
@cross_origin()
def request_run_list():
    db = current_app.config['mongo_col']

    runs = db.find({'session_id': {'$exists': True}}).sort('session_id', pymongo.DESCENDING)

    run_list = []
    for run_obj in runs:
        run = {}
        for key, value in run_obj.items():
            if key == '_id':
                run['document_id'] = str(value)
            else:
                run[key] = value
        run_list.append(run)

    return json.dumps(run_list)

@request_bp.route('/get_latest_run_by_device/<device_oid>', methods=['GET'])
@cross_origin()
def request_latest_run_by_device(device_oid):
    db = current_app.config['mongo_col']

    try:
        device_obj = db.find_one({'_id': ObjectId(device_oid)})
    except InvalidId as e:
        device_obj = None
    if device_obj is None:
        return {}

    run_obj = db.find_one({'session_id': device_obj['last_session_id']})

    device = {}
    for key, value in device_obj.items():
        if key == '_id':
            device['document_id'] = str(value)
        else:
            device[key] = value
    run = {}
    for key, value in run_obj.items():
        if key == '_id':
            run['document_id'] = str(value)
        else:
            run[key] = value

    return json.dumps({'device': device, 'last_run': run})
    # return Response(json.dumps({'device': device_obj, 'last_run': run}, default=json_util.default),
    #             mimetype='application/json')
