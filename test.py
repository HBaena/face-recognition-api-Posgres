import json
from pprint import pprint
from icecream import ic as debug
from DB import OraclePoolConnections
from os import getcwd, path
from cx_Oracle import LOB
from re import sub
from datetime import datetime


pool = OraclePoolConnections(path.join(getcwd(), "connection.yaml"))

scheme = "D911_PADRONES" 
table_names = dict(
    IPH=f"{scheme}.PADRON_IPH",
    PSP=f"{scheme}.PADRON_SEG_PUBLICA",
    SP=f"{scheme}.PADRON_SEG_PUBLICA"
    )

data_str = """
{
    "Message": true,
    "Coincidences": [
        {
            "PADRON_ID": "IPH103",
            "PF_FECHA_REGISTRO": "03/30/2021, 11:18:08",
            "FOTO_ID": 63
        }
    ]
} """

response = json.loads(data_str)
debug(response)


coincidences = response["Coincidences"]

def get_info_by_id(cursor, table_name, id_column, id_):
    query = """
        SELECT *
        FROM %s
        WHERE %s = :%s
    """ % (table_name, id_column, id_column)
    cursor.execute(query, **{id_column: id_})
    col_names = [row[0] for row in cursor.description]
    return {k: v.strftime("%m/%d/%Y, %H:%M:%S") if isinstance(v, datetime) else v for k, v in \
        dict(zip(col_names, cursor.fetchone())).items() if not isinstance(v, LOB)}

out = []
try:
    connection = pool.get_connection()
    cursor = connection.cursor()
    for coincidence in coincidences:
        prefix = sub(r"\d", "", coincidence['PADRON_ID'])
        table_name = table_names[prefix]
        out.append(get_info_by_id(cursor, table_name, f"{prefix}_ID", coincidence['PADRON_ID']))
finally:
    pool.release_connection(connection)

# pprint(response)