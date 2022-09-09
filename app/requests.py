from audioop import cross
from crypt import methods
import json
import statistics
from datetime import datetime

import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId

from flask import Response
from flask import Blueprint
from flask import current_app
from flask import jsonify
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

    return jsonify(device_list)


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

    return jsonify(run_list)


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
    summary_list = []
    pgr_count = 0
    run_count = 0
    aenergy_summ = 0
    for k, v in program_summary.items():
        ret = {
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
            ret['program_aenergy_average'] = float(v['program_aenergy_summ'] / v['program_counter'])
        pgr_count += 1
        aenergy_summ += v['program_aenergy_summ']
        run_count += v['program_counter']
        summary_list.append(ret)
    
    return {
        'count_programs': pgr_count, 
        'count_runs': run_count,
        'aenergy_summ': aenergy_summ, 
        'firstrun_time': first_pgr_run,
        'program_summary': summary_list}


@request_bp.route('/get_time_summary/', methods=['GET'])
@cross_origin()
def request_time_summary():
    db = current_app.config['mongo_col']

    runs = db.find({'program_time_end': {'$exists': True, '$type': 'int'}}).sort('session_id', pymongo.DESCENDING)

    first_pgr_run = 222222222222
    for run_obj in runs:
        if run_obj['program_time_start'] < first_pgr_run:
            first_pgr_run = run_obj['program_time_start']
    first_datetime = datetime.fromtimestamp(first_pgr_run)
    first_year = int(first_datetime.strftime("%Y"))
    first_month = int(first_datetime.strftime("%-m"))
    now_year = int(datetime.now().strftime("%Y"))
    now_month = int(datetime.now().strftime("%-m"))
    # first_year = 2020

    monthly_summary = {}
    # create years and months template
    for y in range(first_year, now_year + 1):
        m_start = first_month if y == first_year else 1
        m_end = now_month if y == now_year else 12
        monthly_summary[y] = {}
        for m in range(m_start, m_end + 1):
            sort_date = "{}.{}.2 04:22".format(y, m)
            monthly_summary[y][m] = {
                'timestamp': datetime.timestamp(datetime.strptime(sort_date, '%Y.%m.%d %H:%M')),
                'year_number': y,
                'month_number': m,
                'monthly_counter': 0,
                'monthly_aenergy': 0.0}       

    runs.rewind()
    for run_obj in runs:
        time = datetime.fromtimestamp(run_obj['program_time_start'])
        year = int(time.strftime("%Y"))
        month = int(time.strftime("%-m"))

        monthly_summary[year][month]['monthly_counter'] += 1
        monthly_summary[year][month]['monthly_aenergy'] += run_obj['machine_aenergy']

    summary_list = []
    for y, months in monthly_summary.items():
        monthly_summary = sorted(list(months.values()), key=lambda d: d['timestamp'], reverse=True)
        summ_count = 0
        for m in monthly_summary:
            summ_count += m['monthly_counter']
        y_obj = {
            'year_number': y,
            'year_program_counter': summ_count,
            'month_count': len(monthly_summary),
            'monthly_summary': monthly_summary}
        summary_list.append(y_obj)
        # summary_list.extend(ye.values())

    # TODO: the '[0]' in the return statment is only a hotfix to not return the data in a list with only one Object
    return jsonify(sorted(summary_list, key=lambda d: d['year_number'], reverse=True))


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

    return {
        'device': device, 
        'last_run': run, 
        'temperature_series': get_temperature_series(device['unique_device_identifier'], db)}


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
