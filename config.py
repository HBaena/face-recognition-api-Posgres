from flask import Flask
from flask_restful import Api  # modules for fast creation of apis
# from flask_sqlalchemy import SQLAlchemy
from os import getcwd, getenv, path
import psycopg2 as psy  # Adding postgrest db handler
from arlp import NumberPlateDetector
from DB import PosgresPoolConnection

EXECUTION_PATH = getcwd()  # Execution path
COMMIT_MODE = getenv('COMMIT_FR_MODE', True)
db_scheme = "padrones"
TABLE_NAMES = dict(
    IPH=f'{db_scheme}."PADRON_IPH"',
    PSP=f'{db_scheme}."PADRON_SEG_PUBLICA"',
    SP=f'{db_scheme}."PADRON_SERVIDOR_PUBLICO"'
    )

def connect_to_db():
    # return OraclePoolConnections(path.join(EXECUTION_PATH, "connection.yaml"))
    return PosgresPoolConnection(path.join(EXECUTION_PATH, "connection.json"))


license_key = path.join(EXECUTION_PATH, 'license.key')  # read the licence.key from current dir
app = Flask(__name__)  # Creating flask app
# db = SQLAlchemy(app)
app.secret_key = "gydasjhfuisuqtyy234897dshfbhsdfg83wt7"
api = Api(app)  # Creating API object from flask app
