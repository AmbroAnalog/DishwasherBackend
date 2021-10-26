import time
from bson.json_util import dumps

from flask import Blueprint
from flask import current_app
from flask import request

request_bp = Blueprint('requests', __name__)


@request_bp.route('/get_all_devices/', methods=['GET'])
def insert_run_state():
    db = current_app.config['mongo_col']

    devices = db.find({'unique_device_identifier': {'$exists': True}})

    return dumps(devices)