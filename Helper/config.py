from typing import Dict
from os.path import exists
from shutil import copy
import yaml


class Dispatcher:
    def __init__(self, data: Dict):
        self.data = data['Dispatcher']

    @property
    def Host(self):
        return self.data['Host']

    @property
    def Port(self):
        return self.data['Port']


class Config:
    FILENAME = 'config.yml'

    data = None

    def __init__(self):
        if self.data is None:
            self.Reload()

    def Reload(self):
        if not exists(self.FILENAME):
            copy('Helper/default_config', self.FILENAME)

        with open(self.FILENAME, 'r', encoding='utf-8') as file:
            self.data = yaml.safe_load(file)

    @property
    def Dispatcher(self):
        return Dispatcher(self.data)

    @property
    def TestCases(self):
        return self.data['TestCases']

    @property
    def UEs(self):
        return self.data['UEs']
