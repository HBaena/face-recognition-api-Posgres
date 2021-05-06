from icecream import ic
from config import TABLE_NAMES, db_scheme
from re import compile as re_compile

def get_templates(cursor):
    try:
                # "FOTO_ID", "PADRON_ID", "PF_FECHA_REGISTRO", "PF_PATRON_RECON"
        query = """
            SELECT              
                "FOTO_ID", "PADRON_ID", "PF_FECHA_REGISTRO", "PF_PATRON_RECON"
            FROM                               
                %s."PADRON_FOTOS"
            ORDER BY "PF_FECHA_REGISTRO" DESC
        """ % (db_scheme, )
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(str(e))
        return -1


def delete_register(cursor, **kwargs):
    table_name = kwargs.pop("TABLE_NAME")
    table_id = kwargs.pop("TABLE_ID")

    query = """
        DELETE FROM %s
        WHERE
            %s = %s
    """ % (
            table_name,
            table_id,
            f":{table_id}"
        )
    try:
        cursor.execute(query, {table_id: kwargs[table_id]})
    finally:
        return


def insert_into(cursor, coord_column=False,  **kwargs):
    from psycopg2 import sql
    table_name = kwargs.pop("TABLE_NAME")
    table_id = kwargs.pop("TABLE_ID")
    query = """
            INSERT INTO %s ( {} %s )
            VALUES ( {} %s )
        
            RETURNING "%s"
            """
    if coord_column:
        coord = kwargs.pop(coord_column)
        str_tmp = (
            f'"{coord_column}",',
            "cn.ST_GeomFromText('POINT(%s %s)', 4326), " % tuple(coord.split())
            )
    else:
         str_tmp = ('', '')
    query = query.format(*str_tmp)

    query = query % (
            table_name,
            ', '.join(map(lambda key: f'"{key}"', kwargs.keys())),  # values prototipe
            ', '.join(map(lambda key: f"%({key})s", kwargs.keys())),  # values prototipe
            table_id
            )
    cursor.execute(sql.SQL(query), kwargs)
    return cursor.fetchone()[0]


def get_info_by_id(cursor, table_name, id_column, id_):
    from icecream import ic
    from psycopg2 import sql
    from datetime import datetime
    from shapely import wkb
    import re
    pattern = r'^.*_'
    prefix_del_pattern = re.compile(pattern)
    prefix_del = lambda col: prefix_del_pattern.sub('', col)

    query = """
            SELECT *
            FROM {}
            WHERE "{}" = %s
        """.format(table_name, id_column)
    cursor.execute(query, (id_, ))

    col_names = [prefix_del(row[0]) for row in cursor.description]
    response =  {k: v.strftime("%m/%d/%Y, %H:%M:%S") if isinstance(v, datetime) else  \
    (lambda coords: (coords.x, coords.y))(wkb.loads(v, hex=True))  if k.upper().count("COORD") else \
    # wkb.loads(v, hex=True).xy  if k.upper().count("COORD") else \
        v for k, v in \
        dict(zip(col_names, cursor.fetchone())).items() if not isinstance(v, memoryview)}

    return response


def transforming_response(coincidences, cursor):
    out = []
    for coincidence in coincidences:
        prefix = sub(r"\d", "", coincidence['PADRON_ID'])
        table_name = TABLE_NAMES[prefix]
        out.append(get_info_by_id(cursor, table_name, f"{prefix}_ID", coincidence['PADRON_ID']))
    return out
