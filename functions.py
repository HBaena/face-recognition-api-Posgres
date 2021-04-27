import numpy as np
from typing import List
from fsdk.flat import FaceTemplate
from cx_Oracle import LOB
from datetime import datetime
from re import sub

db_scheme = "padrones"
table_names = dict(
    IPH=f"{db_scheme}.padron_iph",
    PSP=f"{db_scheme}.padron_seg_publica",
    SP=f"{db_scheme}.padron_servidor_publico"
    )

FACIAL_RECOGNITION_TABLE = ''

citizen_types = ('POLICIA', 'INTERNO', 'FUNCIONARIO', 'CIUDADANO')


# FaceTemplate = c_char*const.FSDK_FACE_TEMPLATE_SIZE

def ctype_to_numpy(ctype_a): return np.frombuffer(ctype_a)


def ctype_from_bytes(bytes):
    array = FaceTemplate()
    array.raw = array.raw.fromhex(bytes.read().hex())
    return array


def array_from_bytes(bytes):
    return np.frombuffer(bytes)


def get_info_by_template_id(cursor, id_: int) -> dict:
    """
    :param id_:
    :param cursor: db cursor
    """
    keys = ('ID_CURP', 'VAR_NOMBRE_CIUDADANO')
    cursor.execute(
        """
        SELECT ID_CURP, VAR_NOMBRE_CIUDADANO 
        FROM MRCTRL_RECON_FACIAL
        WHERE ID_RECON_FACIAL = %s
        """, (id_,)
    )

    return dict(zip(keys, cursor.fetchone()))


# def get_templates(cursor, search: str) -> None:
#     """
#     :param cursor: Db connection
#     :param search: TIPO_CIU to speed the process
#     :return: None (The register are stored on the cursor)
#     """
#     if search:
#         query = (
#             'SELECT A.ID_HIST_RECON_FACIAL, A.ID_RECON_FACIAL, B.ID_CURP, A.TXT_REPORTE, '
#             'B.VAR_NOMBRE_CIUDADANO , A.VAR_TIPO_CIU, A.BYT_PATRON_RECON_FACIAL, A.DAT_FECHA_REGISTRO '
#             'FROM MRCTRL_HIST_RECON_FACIAL A '
#             'LEFT JOIN MRCTRL_RECON_FACIAL B '
#             'ON A.ID_RECON_FACIAL = B.ID_RECON_FACIAL '
#             'WHERE A.VAR_TIPO_CIU in (%s) '
#             'ORDER BY A.DAT_FECHA_REGISTRO DESC'
#         ) % search
#     else:
#         query = (
#             'SELECT A.ID_HIST_RECON_FACIAL, A.ID_RECON_FACIAL, B.ID_CURP, A.TXT_REPORTE, '
#             'B.VAR_NOMBRE_CIUDADANO , A.VAR_TIPO_CIU, A.BYT_PATRON_RECON_FACIAL, A.DAT_FECHA_REGISTRO '
#             'FROM MRCTRL_HIST_RECON_FACIAL A '
#             'LEFT JOIN MRCTRL_RECON_FACIAL B '
#             'ON A.ID_RECON_FACIAL = B.ID_RECON_FACIAL '
#             'ORDER BY A.DAT_FECHA_REGISTRO DESC'
#         )
#     cursor.execute(query)


def image_to_byte_array(img):
    import io
    from PIL import Image
    img = Image.fromarray(img)
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='JPEG')
    img_byte_array = img_byte_array.getvalue()
    return img_byte_array


def numpy_to_image(array: np.array):
    return array


def sort_dict(list_: List[dict], key: str, reverse: bool = False) -> List[dict]:
    return sorted(list_, reverse=reverse, key=lambda k: k[key])


def get_info_by_platenumber(cursor, platenumber: str) -> None:
    query = (
            'SELECT ID_MATRICULA, ID_NUM_MATRICULA, '
            'VAR_NOMBRE_PROPIETARIO, VAR_DIRECCION_PROPIETARIO, '
            'VAR_ANTECEDENTES, TXT_REPORTE '
            'FROM MRCTRL_MATRICULA '
            'WHERE ID_NUM_MATRICULA LIKE \'%s\'; ' % f'%{platenumber}%'
    )
    cursor.execute(query)


def decode_platenumber_info(info):
    return dict(
        ID_MATRICULA=info[0], ID_NUM_MATRICULA=info[1],
        VAR_NOMBRE_PROPIETARIO=info[2], VAR_DIRECCION_PROPIETARIO=info[3],
        VAR_ANTECEDENTES=info[4], TXT_REPORTE=info[-1]
    )


def insert_into_rf(cursor, **kwargs):
    query = """
        SELECT 
        ID_RECON_FACIAL 
        FROM 
            MRCTRL_RECON_FACIAL
        WHERE ID_CURP = '%s'
    """ % kwargs['ID_CURP']
    cursor.execute(query)
    idx = cursor.fetchone()
    if idx:
        return idx[0]

    query = """
    INSERT INTO MRCTRL_RECON_FACIAL
        (ID_CURP, VAR_NOMBRE_CIUDADANO)
    VALUES
        ('{ID_CURP}', '{VAR_NOMBRE_CIUDADANO}')
    RETURNING ID_RECON_FACIAL
    """.format(**kwargs)

    cursor.execute(query)
    return cursor.fetchone()[0]


def insert_into_hist(cursor, **kwargs):
    query = """
        INSERT INTO MRCTRL_HIST_RECON_FACIAL
            (
                ID_RECON_FACIAL, VAR_TIPO_CIU, TXT_REPORTE, 
                BYT_FOTO_CIUDADANO, BYT_PATRON_RECON_FACIAL
            )
        VALUES
            (
                '{ID_RECON_FACIAL}', '{VAR_TIPO_CIU}', '{TXT_REPORTE}', 
                {BYT_FOTO_CIUDADANO}, {BYT_PATRON_RECON_FACIAL}
            )

    """.format(**kwargs)

    cursor.execute(query)


def get_antecedentes(cursor, id_recon_facial):
    query = """
        select
            VAR_TIPO_CIU, TXT_REPORTE, DAT_FECHA_REGISTRO
        FROM 
            MRCTRL_HIST_RECON_FACIAL
        WHERE
            ID_RECON_Facial = %s
    """ % id_recon_facial
    cursor.execute(query)
    return [dict(VAR_TIPO_CIU=tipo, TXT_REPORTE=reporte, DAT_FECHA_REGISTRO=fecha.strftime("%m/%d/%Y, %H:%M:%S")) \
            for tipo, reporte, fecha in cursor.fetchall()]

# ------------------------------------------------------------------

def get_templates(cursor):
    from icecream import ic
    try:
                # "FOTO_ID", "PADRON_ID", "PF_FECHA_REGISTRO", "PF_PATRON_RECON"
        query = """
            SELECT              
                "FOTO_ID", "PADRON_ID", "PF_FECHA_REGISTRO", "PF_PATRON_RECON"
            FROM                               
                padrones."PADRON_FOTOS"
            ORDER BY "PF_FECHA_REGISTRO" DESC
        """
        # ic(str(query))
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
    from icecream import ic
    table_name = kwargs.pop("TABLE_NAME")
    table_id = kwargs.pop("TABLE_ID")
    query = """
            INSERT INTO %s ( {} %s )
            VALUES ( {} %s )
        
            RETURNING "%s"
            """
    if coord_column:
        coord = kwargs.pop(coord_column)
        ic(coord.split())
        str_tmp = (
            f'"{coord_column}",',
            "ST_GeomFromText('POINT(%s %s)', 4326), " % tuple(coord.split())
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
    print(query)
    cursor.execute(sql.SQL(query), kwargs)

    return cursor.fetchone()[0]

def update_coord(cursor, table_name, id_column, 
            idx, coords_column,coords):
    from psycopg2 import sql
    query = sql.SQL("""
            UPDATE {} 
            SET {} = ST_GeomFromText('POINT(%s %s)', 4326)
            WHERE {} = %s
        """).format(
        sql.Identifier(table_name),
        sql.Identifier(coords_column),
        sql.Identifier(id_column),
        )
    cursor.execute(query, (*coords.split(', '), idx))

def get_info_by_id(cursor, table_name, id_column, id_):
    from icecream import ic
    query = """
        SELECT *
        FROM %s
        WHERE %s = :%s
    """ % (table_name, id_column, id_column)
    cursor.execute(query, **{id_column: id_})
    col_names = [row[0] for row in cursor.description]
    return {k: v.strftime("%m/%d/%Y, %H:%M:%S") if isinstance(v, datetime) else v for k, v in \
        dict(zip(col_names, cursor.fetchone())).items() if not isinstance(v, LOB)}


def transforming_response(coincidences, cursor):
    out = []
    for coincidence in coincidences:
        prefix = sub(r"\d", "", coincidence['PADRON_ID'])
        table_name = table_names[prefix]
        out.append(get_info_by_id(cursor, table_name, f"{prefix}_ID", coincidence['PADRON_ID']))
    return out
