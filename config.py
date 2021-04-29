from flask import Flask
from flask_restful import Api  # modules for fast creation of apis
# from flask_sqlalchemy import SQLAlchemy
from os import getcwd, environ, path
import psycopg2 as psy  # Adding postgrest db handler
from arlp import NumberPlateDetector
from DB import PosgresPoolConnection

EXECUTION_PATH = getcwd()  # Execution path
COMMIT_MODE = False
db_scheme = "padrones"
TABLE_NAMES = dict(
    IPH=f"{db_scheme}.padron_iph",
    PSP=f"{db_scheme}.padron_seg_publica",
    SP=f"{db_scheme}.padron_servidor_publico"
    )

def connect_to_db():
    # return OraclePoolConnections(path.join(EXECUTION_PATH, "connection.yaml"))
    return PosgresPoolConnection(path.join(EXECUTION_PATH, "connection.json"))


def create_numberplate_detector():
    runtime_data = path.join(EXECUTION_PATH, "openalpr/runtime_data")
    config = path.join(EXECUTION_PATH, "openalpr/config/openalpr.conf")
    country = "au"
    return NumberPlateDetector(country, config, runtime_data)


license_key = path.join(EXECUTION_PATH, 'license.key')  # read the licence.key from current dir
app = Flask(__name__)  # Creating flask app
# db = SQLAlchemy(app)
app.secret_key = "gydasjhfuisuqtyy234897dshfbhsdfg83wt7"
api = Api(app)  # Creating API object from flask app
