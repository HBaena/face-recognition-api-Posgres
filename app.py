import asyncio
import os

from flask import request  # Flask, receiving data from requests, json handling
from flask_restful import Resource  # modules for fast creation of apis
from config import app, api, license_key, connect_to_db, EXECUTION_PATH, TABLE_NAMES, db_scheme
from luxand import init, image_from_jpg, get_face_template, image_face_recognition, VideoFaceRecognition
from functions import ctype_to_numpy, sort_dict, transforming_response
from model import insert_into, delete_register, get_templates
from icecream import ic as debug
# from apscheduler.schedulers.background import BackgroundScheduler

# from PIL import Image  # module for image handling
# import pickle


threshold = 0.92  # Needs a 92% of similarity to match
pool = None
# np_detector = None

loop = asyncio.new_event_loop()  # Create thread
asyncio.set_event_loop(loop)  # Set the created thread as asyncio thread


def refresh_templates() :
    from model import get_templates
    try:
        connection = pool.get_connection()  # Stablish connection
        cursor = connection.cursor()  # Get cursor connection
        video_fr = VideoFaceRecognition()
        templates = get_templates(cursor)
        video_fr.templates = templates
        # response = image_face_recognition(img, templates, cursor, threshold)  # It Does FR from image
    except Exception as e:
        pool.release_connection(connection)  # release db connection    video_fr.templates = cursor.fetchall()
        return dict(Message=False, Error="DB error", log=str(e))
    finally:
        pool.release_connection(connection)  # release db connection    video_fr.templates = cursor.fetchall()


@app.before_first_request
def initialize() -> None:
    """
    Initialize FSDK by a license and connect to db
    :return: None
    """
    global pool
    # ray.init()
    pool = connect_to_db()
    refresh_templates()
    init(license_key)

    # scheduler = BackgroundScheduler()
    # job = scheduler.add_job(refresh_templates, 'interval', minutes=15)
    # scheduler.start()
    # refresh_templates()


@app.after_request
def after_request(response) -> dict:
    """
    Prevent CORS problems after each request
    :param response: Response of any request
    :return: The same request
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


class MirosCNFaceRecognition(Resource):
    """
        SearchFace API from flask_restful
        Using flask_restful to develop faster
        Defining request methods ass class methods
    """

    def post(self):
        """
        POST request method, receive an image and return
        :return: Json containing Message=bool, Error=str,log=Exception, coincidence/possibilities=dictionary
        """
        global pool
        search = request.form.get('search', None)

        if request.files:  # If an image or a video is received, face recognition will be done
            image = request.files.get('image', None)
            video = request.files.get('video', None)

            if image:
                from re import sub
                from icecream import ic
                table_names = dict(
                    IPH=f"PADRON_IPH",
                    PSP=f"PADRON_SEG_PUBLICA",
                    SP=f"PADRON_SERVIDOR_PUBLICO"
                    )
                try:
                    image = image.read()
                    img = image_from_jpg(image)  # convert binary image into fsdk image
                    try:
                        connection = pool.get_connection()  # Stablish connection
                        cursor = connection.cursor()  # Get cursor connection 
                        templates = get_templates(cursor)
                        response = image_face_recognition(img, templates, cursor, threshold)  # It Does FR from image
                        if not response['Error']:
                            ic()
                            response['Coincidences'] = list(response['Coincidences'].values())
                            ic()
                            coincidences = response["Coincidences"]
                            response["Coincidences"] = transforming_response(coincidences, cursor)
                            response["Status"] = table_names[sub( r'\d','' ,list(response["Coincidences"][0].values())[0])]
                            return response
                        else:
                            return dict(
                                Message=False,
                                Error='No coincidences',
                            )
                    except Exception as e:
                        pool.release_connection(connection)  # release db connection
                        return dict(Message=False, Error="DB error", log=str(e))
                    finally:
                        pool.release_connection(connection)  # release db connection

                except Exception as e:                    
                    return dict(
                        Message=False,
                        Error='Any face was found',
                        log=str(e)
                    )
            elif video:
                try:
                    import time
                    tempfile = os.path.join(EXECUTION_PATH, f'temp/{time.time()}.mp4')
                    print(tempfile)
                    with open(tempfile, "wb") as out_file:  # Temporary video file
                        out_file.write(request.files['video'].read())
                    # Valid values for mode
                    # fast (1 frame per second)
                    # normal (3 frame per second)
                    # deep (10 frame per second)
                    mode = request.form.get('mode', 'normal')  # If no mode argument is received normal is put
                    try:
                        video_fr = VideoFaceRecognition()  # Create a video face recognition object
                        connection = pool.get_connection()  # Stablish connection
                        cursor = connection.cursor()  # Get cursor connection
                        templates = get_templates(cursor)  # 
                        video_fr.templates = templates
                        # response = image_face_recognition(img, templates, cursor, threshold)  # It Does FR from image
                        video_fr.load_video(tempfile)  # load temporary video file
                        response = loop.run_until_complete(video_fr.process(threshold, mode))  # Run video FR asynchronously
                        coincidences = response["Coincidences"]
                        response["Coincidences"] = transforming_response(coincidences, cursor)
                        try:
                            os.remove(tempfile)
                        finally:
                            pool.release_connection(connection)  # release db connection    video_fr.templates = cursor.fetchall()
                            return response  # Return video FR response
                    except Exception as e:
                        pool.release_connection(connection)  # release db connection    video_fr.templates = cursor.fetchall()
                        return dict(Message=False, Error="DB error", log=str(e))
                except Exception as e:
                    return dict(Message=False, Error="Error from video recognition", log=str(e))
        else:
            return dict(Mesage=False, Error='Any file was received.')

    def put(self):
        """
        PUT request method that receive an image and get the face template
        Assumes that the image just contains one face
        :return: Json containing status=bool, Error/Message=str, log=Exception, array=numpy.array
        """
        from pprint import pprint
        from psycopg2 import Binary
        from datetime import datetime
        from icecream import ic
        global pool


        form = dict(request.form)
        files = dict(request.files)


        try:
            files = {k: file.read() for k, file in files.items()}
        except Exception as e:
            return dict(Message=False, Error="Problems while reading files", log=str(e))

        prefix = form.pop("TABLE")
        table_name = TABLE_NAMES[prefix]
        table_id = f'{prefix}_ID'
        padron_fotos = dict()
        padron_fotos["PF_FOTO"] = files.pop("PF_FOTO")
        # padron_fotos["PF_FECHA_REGISTRO"] = datetime.now()
        padron_fotos["PADRON_ID"] = None
        padron_fotos["TABLE_NAME"] = f'{db_scheme}."PADRON_FOTOS"' 
        padron_fotos["TABLE_ID"] = 'FOTO_ID'

        padron = {**files, **form}
        coord_column = padron.get('COORD_COLUMN', False)
        if coord_column:
            del padron['COORD_COLUMN']
        padron[f"{prefix}_FOTO"] = padron_fotos["PF_FOTO"]
        padron["TABLE_NAME"] = table_name 
        padron["TABLE_ID"] = table_id


        try:
            image = image_from_jpg(padron_fotos["PF_FOTO"])  # Convert bytes image to FSDK
        except Exception as e:
            return dict(Message=False, Error='Impossible to read theimage (it is not a JPG/JPEG file)', log=str(e))
        
        try:
            template = ctype_to_numpy(get_face_template(image))  # RF template
            padron_fotos["PF_PATRON_RECON"] = template.tobytes()
        except Exception as e:
            return dict(Message=False, Error='Any face was found, take a better picture', log=str(e))

        try:
            try:
                connection = pool.get_connection()
                connection.autocommit = False
                cursor = connection.cursor()
                padron_fotos["PADRON_ID"] = insert_into(cursor, coord_column, **padron)
                # connection.commit()
                idx = insert_into(cursor, **padron_fotos)
                # connection.commit()  # Making changes to db
            except Exception as e:
                # delete_register(cursor, **padron)
                # pool.release_connection(connection)
                return dict(Message=False, Error=f"Error while inserting data to 'PADRON FOTOS'", log=str(e))
            finally:
                pool.release_connection(connection)
            return dict(Mesagge="All fine", ID=idx)
        except Exception as e:
            return dict(Message=False, Error='An error occurred while inserting the report. Try later', log=str(e))

    def get(self):
        from pprint import pprint
        from functions import array_from_bytes, ctype_from_bytes
        try:
            connection = pool.get_connection()
            cursor = connection.cursor()
            templates = get_templates(cursor)
            pprint(templates)
            # for i_, idx, date, template in templates:
        except Exception as e:
            print(e)
        finally:
            pool.release_connection(connection)

        return dict(Message='Face recognition api')


# Add end point to the API
api.add_resource(MirosCNFaceRecognition, '/robot/face-recognition/')

if __name__ == '__main__':
    # Run the app as development
    # This is modified by changing the environment var FLASK_ENV to production

    app.run(host='0.0.0.0', debug=True, threaded=True)
