import json
from psycopg2 import pool
import cx_Oracle
import logging
from os import getcwd, path

logging.basicConfig(filename='db.log', level=logging.DEBUG)

class PoolConection:
    def __init__(self,config_filename):
        raise NotImplementedError

    def get_connection(self):
        raise NotImplementedError

    def release_connection(self):
        raise NotImplementedError




class OraclePoolConnections:
    """docstring for Oracle_connection"""
    def __init__(self, config_filename):
        self.config_filename = config_filename
        with open(path.join(getcwd(), "connection.json"),  "r") as file:
            db_args = json.loads(file.read())
            user = db_args.pop("user")
            psw = db_args.pop("psw")
            pool_size = db_args.pop("pool_size")
            client_path = db_args.pop("client_path")


        cx_Oracle.init_oracle_client(lib_dir=client_path)  # initialize oracle client

        str_connection = "{host}:{port}/{sid}".format(**db_args)
        self.pool = cx_Oracle.SessionPool(user, psw, str_connection, min=pool_size, max=pool_size, 
            increment=0, encoding="UTF-8")


    def get_connection(self):
        return self.pool.acquire()


    def release_connection(self, connection):
        try:
            self.pool.release(connection)
            return True
        except Exception as _:
            return False


    def __del__(self):
        self.pool.close()

class PosgresPoolConnection(PoolConection):

    def __init__(self, config_filename):
        with open(config_filename, "r") as file:
            db_args = json.loads(file.read())
            pool_size = db_args.pop("pool_size")
        self.pool = pool.ThreadedConnectionPool(
            minconn=pool_size,
            maxconn=pool_size,
            **db_args
        )

    def get_connection(self):
        return self.pool.getconn()

    def release_connection(self, connection):
        try:
            self.pool.putconn(connection)
            return True
        except Exception as e:
            logging.debug(str(e))
            return False

    def  __del__(self):
        try:
            self.pool.closeall()
            return True
        except Exception as e:
            logging.debug(str(e))
            return False
