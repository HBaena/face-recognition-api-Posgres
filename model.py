from icecream import ic
from config import TABLE_NAMES

def get_templates(cursor):
    try:
                # "FOTO_ID", "PADRON_ID", "PF_FECHA_REGISTRO", "PF_PATRON_RECON"
        query = """
            SELECT              
                "FOTO_ID", "PADRON_ID", "PF_FECHA_REGISTRO", "PF_PATRON_RECON"
            FROM                               
                padrones."PADRON_FOTOS"
            ORDER BY "PF_FECHA_REGISTRO" DESC
        """
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

def transforming_response(coincidences, cursor):
    out = []
    for coincidence in coincidences:
        prefix = sub(r"\d", "", coincidence['PADRON_ID'])
        table_name = TABLE_NAMES[prefix]
        out.append(get_info_by_id(cursor, table_name, f"{prefix}_ID", coincidence['PADRON_ID']))
    return out
