import yaml
import os
import pymongo
from flask import Flask
#from flask_socketio import SocketIO, emit, send
from flask_socketio import SocketIO
from flask_socketio import emit
from flask_socketio import send
from flask_cors import CORS, cross_origin
# https://stackoverflow.com/questions/25594893/how-to-enable-cors-in-flask

from bp_insert import insert_bp
from bp_requests import request_bp
from bp_notification import notify_bp

from subscription_db import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TestKey'
app.config['CORS_HEADERS'] = 'Content-Type'

socketio = SocketIO(app, cors_allowed_origins='*', path='/live/socket.io')
socketio_clients = 0

app.register_blueprint(insert_bp, url_prefix='/insert')
app.register_blueprint(request_bp, url_prefix='/request')
app.register_blueprint(notify_bp, url_prefix='/notify')

cors = CORS(app, resources={r"/*":{"origins":"*"}})

@app.route('/health', methods=['GET'])
def health_check():
    db = app.config['mongo_col']
    count = db.count_documents({})
    notify_db_count = len(USER_SUBSCRIPTION_STORAGE)

    if count and count > 0:
        return { 'success': True, 'database_collection_count': count, 'database_notification_count': notify_db_count}
    else:
        return { 'success': False }


def load_config():
    folder = os.path.dirname(os.path.realpath(__file__))
    with open(folder + '/configuration.yaml', 'r') as file:
        cfg = yaml.safe_load(file)

    if cfg is None:
        return

    connection_string = "mongodb://{user}:{passw}@{server}:{port}/".format(user=cfg['database']['user'], passw=cfg['database']['password'], server=cfg['database']['server'], port=cfg['database']['port'])
    mongo_client = pymongo.MongoClient(connection_string)
    mongo_db = mongo_client[cfg['database']['database']]
    mongo_col = mongo_db[cfg['database']['collection']]

    app.logger.info('load database object')
    app.config['mongo_col'] = mongo_col


@socketio.on('connect')
def connect_handler():
    app.config['connected_clients'] += 1
    socketio.emit('my response', {'data': 'Connected'})
    print('client number {} connected'.format(app.config['connected_clients']))


@socketio.on('disconnect')
def disconnect_handler():
    app.config['connected_clients'] -= 1
    print('client disconnect...')


load_config()
app.config['connected_clients'] = 0
app.config['socketio'] = socketio

if __name__ == '__main__':
    socketio.run(app, debug=True)

