import random


class Question:

    def __init__(self, text, answer, answer_units):
        self.text = text
        self.answer = answer
        self.answer_units = answer_units


    def is_trick(self):
        return len(self.answer) == 0


class UsuableDataError(Exception):
    pass


class QuestionColllector:

    def __init__(self, metar):
        self.metar = metar
        self.questions = {}


    def generate_airport_question(self):
        try:
            if self.metar['station'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['airport'] = Question('What is the airport ICAO?',
                                                [self.metar['station']],
                                                '')
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_time_question(self):
        try:
            if self.metar['time']['repr'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['time'] = Question('What is time was this METAR report made?',
                                              ['{0} {1}'.format(self.metar['time']['repr'][2:-1], 'ZULU')],
                                              'ZULU')
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_wind_direction_question(self):
        try:
            if self.metar['wind_direction']['value'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['wind_direction'] = Question('What is the wind direction?',
                                                        ['{0} {1}'.format(self.metar['wind_direction']['value'], 'degrees')],
                                                        'degrees')
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_wind_speed_question(self):
        try:
            if self.metar['wind_speed']['value'] is None or self.metar['units']['wind_speed'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['wind_speed'] = Question('What is the wind speed?',
                                                    ['{0} {1}'.format(self.metar['wind_speed']['value'], self.metar['units']['wind_speed'])],
                                                    self.metar['units']['wind_speed'])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_wind_gust_question(self):
        try:
            if self.metar['units']['wind_speed'] is None:
                raise UsuableDataError('Data is not unusable')

            question = Question('What is the wind gusting to?',
                                [],
                                self.metar['units']['wind_speed'])
            if self.metar['wind_gust'] is not None:
                question.answer.append('{0} {1}'.format(self.metar['wind_gust']['value'], self.metar['units']['wind_speed']))
            else:
                question.answer.append('The wind is not currently gusting.')
            self.questions['wind_gust'] = question
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_altimiter_question(self):
        try:
            if self.metar['altimeter']['value'] is None or self.metar['units']['altimeter'] is None:
                raise UsuableDataError('Data is not unusable')

            self.question = Question('What is the altimiter?',
                                     ['{0} {1}'.format(self.metar['altimeter']['value'], self.metar['units']['altimeter'])],
                                     self.metar['units']['altimeter'])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_temperature_question(self):
        try:
            if self.metar['temperature']['value'] is None or self.metar['units']['temperature'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['temperature'] = Question('What is the temperature?',
                                                     ['{0} {1}'.format(self.metar['temperature']['value'], self.metar['units']['temperature'])],
                                                     self.metar['units']['temperature'])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_dewpoint_question(self):
        try:
            if self.metar['dewpoint']['value'] is None or self.metar['units']['temperature'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['dewpoint'] = Question('What is the dewpoint?',
                                                  ['{0} {1}'.format(self.metar['dewpoint']['value'], self.metar['units']['temperature'])],
                                                  self.metar['units']['temperature'])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_visability_question(self):
        try:
            if self.metar['visibility']['value'] is None or self.metar['units']['visibility'] is None:
                raise UsuableDataError('Data is not unusable')

            self.questions['visibility'] = Question('What is the visiability?',
                                                    ['{0} {1}'.format(self.metar['visibility']['value'], self.metar['units']['visibility'])],
                                                    self.metar['units']['visibility'])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_cloud_coverage_question(self):
        try:
            if self.metar['clouds'] is None or len(self.metar['clouds']) == 0:
                raise UsuableDataError('Data is not unusable')

            coverage = []
            conversion = {'SKC' : 'Sky Clear',
                          'NDC' : 'NIL Cloud Detected',
                          'CLR' : 'No Clouds Below 12,000 ft',
                          'FEW' : 'Few Clouds',
                          'SCT' : 'Scattered Clouds',
                          'BKN' : 'Broken Clouds',
                          'OVC' : 'Overcast Clouds',
                          'VV' : 'Vertical Visability Warning'}
            for item in self.metar['clouds']:
                if conversion[item['type']] not in coverage:
                    coverage.append(conversion[item['type']])
            self.questions['cloud_coverage'] = Question('What is the reported cloud coverage?',
                                                        coverage,
                                                        '')
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_cloud_height_question(self, cloud):
        try:
            if self.metar['clouds'] is None or len(self.metar['clouds']) == 0 or self.metar['units']['altitude'] is None:
                raise UsuableDataError('Data is not unusable')

            heights = []
            for item in self.metar['clouds']:
                if item['type'] == cloud:
                    heights.append(item['altitude'])

            if len(heights) > 0:
                conversion = {'FEW' : 'few',
                            'SCT' : 'scattered',
                            'BKN' : 'broken',
                            'OVC' : 'overcast'}
                question = Question('What is the height of the {0} clouds?'.format(conversion[cloud]),
                                    [],
                                    self.metar['units']['altitude'])
                for item in sorted(heights):
                    question.answer.append('{0}00 {1}'.format(item, self.metar['units']['altitude']))
                self.questions['cloud_{0}_heights'.format(conversion[cloud])] = question
                return heights
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_cloud_ceiling_questions(self, cloud):
        try:
            if self.metar['clouds'] is None or len(self.metar['clouds']) == 0 or self.metar['units']['altitude'] is None:
                raise UsuableDataError('Data is not unusable')

            conversion = {'FEW' : 'few',
                          'SCT' : 'scattered',
                          'BKN' : 'broken',
                          'OVC' : 'overcast'}
            for count, item in enumerate(self.metar['clouds']):
                self.questions['cloud_{0}_ceiling_{1}'.format(item['type'], count)] = Question('What kind of clouds have a ceiling of {0}00 {1}?'.format(item['altitude'], self.metar['units']['altitude']),
                                                                                               [conversion[item['type']].capitalize()],
                                                                                               self.metar['units']['altitude'])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_questions(self):
        self.generate_airport_question()
        self.generate_time_question()
        self.generate_wind_direction_question()
        self.generate_wind_speed_question()
        self.generate_wind_gust_question()
        self.generate_altimiter_question()
        self.generate_temperature_question()
        self.generate_cloud_coverage_question()
        for cloud in ['FEW', 'SCT', 'OVC', 'BKN']:
            self.generate_cloud_height_question(cloud)
            self.generate_cloud_ceiling_questions(cloud)

        chosen_questions = []
        for question in random.sample(list(self.questions.values()), k=5):
            chosen_questions.append(question.__dict__)

        if len(chosen_questions) == 0:
            return None
        else:
            return chosen_questions
