from fsdk import FSDK
import os
import pickle
import ctypes
from functions import numpy_to_image, image_to_byte_array
import asyncio
import cv2
import logging
logging.basicConfig(filename='fr.log', level=logging.DEBUG)

from functions import ctype_from_bytes


def save_templates(db_path, templates):
    with open(os.path.join(db_path, 'templates.pkl'), 'wb') as handle:
        pickle.dump(templates, handle, protocol=pickle.HIGHEST_PROTOCOL)


def save_directory(db_path, templates):
    with open(os.path.join(db_path, 'templates.pkl'), 'wb') as handle:
        pickle.dump(set(templates.keys()), handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_templates(db_path):
    return pickle.load(open(os.path.join(db_path, 'templates.pkl'), 'rb'))


def load_directory(db_path):
    return pickle.load(open(os.path.join(db_path, 'directory.pkl'), 'rb'))


def to_ctype(data):
    return data.ctypes.data_as(ctypes.POINTER(FSDK.FaceTemplate)).contents


def init(license_):
    try:
        FSDK.ActivateLibrary(open(license_).read())
        print(FSDK.GetLicenseInfo())
    except Exception as e:
        print(f'Lincense error: {e}')
        exit()

    FSDK.Initialize()


def compare_faces(img_1, img_2):
    return FSDK.MatchFaces(img_1, img_2)


def image_from_jpg(buffer):
    return FSDK.LoadImageFromJpegBuffer(buffer)


def get_face_template(img):
    return FSDK.GetFaceTemplate(img)


def get_faces(img):
    return img.DetectMultipleFaces()


def init_video(license_, **kwargs):
    init(license_)
    tracker = FSDK.Tracker()  # creating a FSDK Tracker
    tracker.SetParameters(**kwargs)
    return tracker


async def find_from_video(img, templates, mode='all', threshold=0.90):
    faces = get_faces(img)
    for face in faces:
        tmp = FSDK.GetFaceTemplateInRegion(img, face)
        for name, features in templates.items():
            similarity = FSDK.MatchFaces(tmp, to_ctype(features))
            # print(similarity)
            if similarity > threshold:
                print(img, name, similarity)
                # if mode
        tmp.Free()
    img.Free()


def close():
    FSDK.Finalize()


def close_video(tracker):
    # tracker.SaveToFile(os.path.join(db_path, 'tracker_memory.dat'))
    tracker.Free()
    FSDK.Finalize()


def image_face_recognition(img, templates, cursor, threshold: float) -> dict:
    # Find template from image
    faces, current_templates = get_faces(img), []  # List of faces and list of templates
    for face in faces:
        # try:
        current_templates.append(FSDK.GetFaceTemplateInRegion(img, face))  # Find face template for each face
        # except Exception as e:
        #     print(str(e))
    if not current_templates:  # If no faces are found, return an error
        return dict(Message=False, Error='Any face was found')
    coincidences = dict()  # Coincidences with more tha threshold% of similarity
    i = 0
    for item in templates:
        i += 1
        # id_hist, id_, curp, report, name, type_, template_db, date_ = item  # HRF_RF_ID, HRF_TIPO_CIU, MRF_PATRON_F
        id_hist, id_, date_, template_db = item 
        template_db = ctype_from_bytes(template_db.hex())  # Create an array from bytes and then convert into ctype
        # if id_ in coincidences:
        #     continue
        for template in current_templates:
            similarity = compare_faces(template, template_db)  # Comparing faces
            if similarity > threshold:
                if coincidences.get(id_, None) is None:
                    coincidences[id_] = dict(
                            PADRON_ID=id_, PF_FECHA_REGISTRO=date_.strftime("%m/%d/%Y, %H:%M:%S"),
                            FOTO_ID=id_hist
                        )


    if not coincidences:
        return dict(Message=False, Error='No coincidence')

    else:
        return dict(
            Message=True,  # Message of successful task
            Error=False,
            Coincidences=coincidences,
        )


async def video_face_recognition(img, templates, cursor, threshold: float) -> dict:
    response = image_face_recognition(img, templates, cursor, threshold)
    if not response['Message']:
        return dict()
    else:
        del response['Message'], response['Error']
        return response


async def process_frame(frame):
    img = numpy_to_image(frame)  # Converting frame to image (numpy to Pillow image)
    img = image_to_byte_array(img)  # Image to Jpeg buffer
    return img


class VideoFaceRecognition:
    """docstring for LiveRecognition"""

    def __init__(self, templates=None, video=None):
        self.video = video
        self.templates = templates
        self.camera = cv2.VideoCapture()
        self.frame = None

    def load_video(self, video):
        try:
            self.camera.release()
        except:
            pass
        self.video = video
        self.camera.open(self.video)

    def grab_frame(self):
        ret, frame = self.camera.read()
        self.frame = frame
        return ret

    def show_image(self):
        cv2.imshow('Video', self.frame)

    # noinspection PyUnresolvedReferences
    async def process(self, thershold=0.95, mode='fast'):
        from pprint import pprint
        frames_per_second = 1 if mode == 'fast' else 5 if mode == 'deep' else 3
        tasks = list()
        frames = int(self.camera.get(7))
        images = []
        for i in range(0, frames, int(30 / frames_per_second)):
            self.camera.set(1, i)
            ret = self.grab_frame()  # Get frame
            # self.show_image() # Show frame
            if not ret:
                break
            images.append(process_frame(self.frame))
        images = await asyncio.gather(*images, return_exceptions=True)
        for img in images:
            tasks.append(video_face_recognition(FSDK.LoadImageFromJpegBuffer(img), self.templates, None, thershold))
        response = await asyncio.gather(*tasks, return_exceptions=True)
        # logging.debug(str(response))
        out = dict(Message=False, Coincidences=dict())

        for d in response:
            if not d:
                continue
            for key, value in d.items():
                out[key].update(value)

        if out['Coincidences']:
            out['Message'] = True
            out['Coincidences'] = list(out['Coincidences'].values())
        return out

    def __del__(self):
        self.camera.release()
