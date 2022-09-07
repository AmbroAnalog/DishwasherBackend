from audioop import cross
from crypt import methods
import json
import statistics

import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId

from flask import Response
from flask import Blueprint
from flask import current_app
from flask_cors import CORS, cross_origin

request_bp = Blueprint('requests', __name__)


@request_bp.route('/get_all_devices/', methods=['GET'])
@cross_origin()
def request_device_list():
    db = current_app.config['mongo_col']

    devices = db.find({'series_name': 'device'})

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

    runs = db.find({'program_runtime': {'$exists': True}}).sort('session_id', pymongo.DESCENDING)

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


@request_bp.route('/get_program_summary/', methods=['GET'])
@cross_origin()
def request_program_summary():
    db = current_app.config['mongo_col']

    runs = db.find({'program_time_end': {'$exists': True, '$type': 'int'}}).sort('session_id', pymongo.DESCENDING)

    program_summary = {}
    first_pgr_run = 222222222222
    for run_obj in runs:
        id = run_obj['program_selected_id']
        if id in program_summary:
            # program entry already exists
            program_summary[id]['program_counter'] += 1
            program_summary[id]['program_runtime_list'].append(run_obj['program_runtime'])
            program_summary[id]['program_estimated_summ'] += run_obj['program_estimated_runtime']
            if run_obj['machine_aenergy'] is not None:
                program_summary[id]['program_aenergy_summ'] += run_obj['machine_aenergy']
                program_summary[id]['program_aenergy_ct'] += 1
            if run_obj['program_time_start'] > program_summary[id]['program_last_run']:
                program_summary[id]['program_time_start'] = run_obj['program_time_start']
        else:
            program_summary[id] = {
                'program_id': id,
                'program_counter': 1,
                'program_last_run': run_obj['program_time_start'],
                'program_runtime_list': [run_obj['program_runtime']],
                'program_estimated_summ': run_obj['program_estimated_runtime']}
            if run_obj['machine_aenergy'] is not None:
                program_summary[id]['program_aenergy_summ'] = run_obj['machine_aenergy']
                program_summary[id]['program_aenergy_ct'] = 1
            else:
                program_summary[id]['program_aenergy_summ'] = 0
                program_summary[id]['program_aenergy_ct'] = 0
        if run_obj['program_time_start'] < first_pgr_run:
            first_pgr_run = run_obj['program_time_start']

    program_summary = dict(sorted(program_summary.items()))
    ret = []
    pgr_count = 0
    run_count = 0
    aenergy_summ = 0
    for k, v in program_summary.items():
        summary = {
            'program_id': v['program_id'],
            'program_counter': v['program_counter'],
            'program_last_run': v['program_last_run'],
            'program_runtime_average': statistics.fmean(v['program_runtime_list']),
            'program_runtime_stdev': statistics.stdev(v['program_runtime_list']) if len(v['program_runtime_list']) > 1 else 0.0,
            'program_estimated_average': float(v['program_estimated_summ'] / v['program_counter']),
            'program_aenergy_average': 0.0,
            'program_aenergy_summ': v['program_aenergy_summ']
        }
        if v['program_aenergy_ct'] > 0:
            summary['program_aenergy_average'] = float(v['program_aenergy_summ'] / v['program_counter'])
        ret.append(summary)
        pgr_count += 1
        aenergy_summ += v['program_aenergy_summ']
        run_count += v['program_counter']
    
    return json.dumps({
        'count_programs': pgr_count, 
        'count_runs': run_count,
        'aenergy_summ': aenergy_summ, 
        'firstrun_time': first_pgr_run,
        'program_summary': ret})


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
    if run_obj is not None:
        for key, value in run_obj.items():
            if key == '_id':
                run['document_id'] = str(value)
            else:
                run[key] = value

    return json.dumps({'device': device, 'last_run': run, 'temperature_series': get_temperature_series(device['unique_device_identifier'], db)})
    # return Response(json.dumps({'device': device_obj, 'last_run': run}, default=json_util.default),
    #             mimetype='application/json')


def get_temperature_series(device_identifier, db):
    temp_series = db.find_one({'unique_device_identifier': device_identifier, 'series_name': 'temperature_series'})
    data = {}
    if temp_series is None:
        return data
    for key, value in temp_series.items():
        if key == '_id':
            data['document_id'] = str(value)
        else:
            data[key] = value

    return data
