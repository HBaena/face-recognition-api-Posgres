from openalpr import Alpr


class NumberPlateDetector(Alpr):
    """docstring for NumberPlateDetector"""

    def __init__(self, country, config, runtime_data, top_n=5):
        super(NumberPlateDetector, self).__init__(country, config, runtime_data)
        self.country = country
        self.config = config
        self.runtime_data = runtime_data
        self.set_top_n(top_n)
        self.set_default_region(country)
        self.set_detect_region(False)

    @staticmethod
    def decode(results):
        for plate in results['results']:
            for candidate in plate['candidates']:
                yield candidate['plate'], candidate['confidence']
