# from openalpr import Alpr
from requests import post
from json import loads
# class NumberPlateDetector(Alpr):
#     """docstring for NumberPlateDetector"""

#     def __init__(self, country, config, runtime_data, top_n=5):
#         super(NumberPlateDetector, self).__init__(country, config, runtime_data)
#         self.country = country
#         self.config = config
#         self.runtime_data = runtime_data
#         self.set_top_n(top_n)
#         self.set_default_region(country)
#         self.set_detect_region(False)

#     @staticmethod
#     def decode(results):
#         for plate in results['results']:
#             for candidate in plate['candidates']:
#                 yield candidate['plate'], candidate['confidence']


class NumberPlateDetector:
    """docstring for ALPR"""
    def __init__(self):
        token = r'Token bc4a862b33dde9ac70658c4ebf238a7ca2f75daf'
        self.url =  r'https://api.platerecognizer.com/v1/plate-reader/'
        self.headers = dict(Authorization=token)
        self.data = dict(regions='mx')

    def get_license_plate(self, image):
        response = post(self.url, data=self.data, headers=self.headers, files=dict(upload=image))
        response = loads(response.text)
        results = response.get("results", None)
        if results:
            return results[0].get("candidates", list())