import time
import json
from bson.json_util import dumps
from bson import json_util
from bson.objectid import ObjectId
from bson.errors import InvalidId

from flask import Response
from flask import Blueprint
from flask import current_app
from flask import request

request_bp = Blueprint('requests', __name__)


@request_bp.route('/get_all_devices/', methods=['GET'])
def request_device_list():
    db = current_app.config['mongo_col']

    devices = db.find({'unique_device_identifier': {'$exists': True}})

    return dumps(devices)

@request_bp.route('/get_all_runs/', methods=['GET'])
def request_run_list():
    db = current_app.config['mongo_col']

    runs = db.find({'session_id': {'$exists': True}}).sort('session_id')

    return dumps(runs)

@request_bp.route('/get_latest_run_by_device/<device_oid>', methods=['GET'])
def request_latest_run_by_device(device_oid):
    db = current_app.config['mongo_col']

    try:
        device_obj = db.find_one({'_id': ObjectId(device_oid)})
    except InvalidId as e:
        device_obj = None
    if device_obj is None:
        return {}

    run = db.find_one({'session_id': device_obj['last_session_id']})
    return Response(json.dumps({'device': device_obj, 'last_run': run}, default=json_util.default),
                mimetype='application/json')
