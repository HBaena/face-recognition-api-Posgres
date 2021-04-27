import json
import cx_Oracle

class OraclePoolConnections:
    """docstring for Oracle_connection"""
    def __init__(self, config_filename):
        self.config_filename = config_filename
        with open("connection.json", "r") as file:
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