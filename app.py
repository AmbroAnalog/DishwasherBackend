import yaml
import os
import pymongo
from flask import Flask

from insert import insert_bp

app = Flask(__name__)
 
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

if __name__ == "__main__":
    load_config()
    app.run(debug=True, host='45.156.84.32')
