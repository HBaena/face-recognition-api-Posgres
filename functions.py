import numpy as np
from typing import List
from fsdk.flat import FaceTemplate
from cx_Oracle import LOB
from datetime import datetime
from re import sub
from config import TABLE_NAMES
from model import get_info_by_id

# FaceTemplate = c_char*const.FSDK_FACE_TEMPLATE_SIZE

def ctype_to_numpy(ctype_a): return np.frombuffer(ctype_a)


def ctype_from_bytes(bytes_):
    array = FaceTemplate()
    array.raw = array.raw.fromhex(bytes_)
    return array


def array_from_bytes(bytes_):
    return np.frombuffer(bytes_)


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


def transforming_response(coincidences, cursor):
    out = []
    for coincidence in coincidences:
        prefix = sub(r"\d", "", coincidence['PADRON_ID'])
        table_name = TABLE_NAMES[prefix]
        out.append(get_info_by_id(cursor, table_name, f"{prefix}_ID", coincidence['PADRON_ID']))
    return out
