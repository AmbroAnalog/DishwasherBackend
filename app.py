import yaml
import os
import pymongo
from flask import Flask
from flask_socketio import SocketIO, emit, send

from insert import insert_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TestKey'

socketio = SocketIO(app, cors_allowd_origins='*')
socketio_clients = 0

app.register_blueprint(insert_bp, url_prefix='/insert')


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


@app.route('/api/socket')
def index():
    print('route socket init')
    print('What to do her???')


@socketio.on('connect')
def test_connect():
    app.config['connected_clients'] += 1
    print('Client connected test')


@socketio.on('new-message')
def handle_message(msg):
    print('received message: ' + msg)


@socketio.on('new-message-s')
def send_data():
    print('send_data???')
    pass


@socketio.on('disconnect')
def test_disconnect():
    app.config['connected_clients'] -= 1
    print('Client disconnect')


if __name__ == "__main__":
    load_config()
    app.config['connected_clients'] = 0
    app.config['socketio'] = socketio
    # app.run(debug=True, host='45.156.84.32')
    socketio.run(app, host='45.156.84.32')
