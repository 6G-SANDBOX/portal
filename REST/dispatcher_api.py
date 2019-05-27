from .rest_client import RestClient
from app.models import Experiment

import json


class Dispatcher_Api(RestClient):

    def __init__(self, api_host, api_port, suffix):
        super().__init__(api_host, api_port, suffix)

    def Post(self, experiment_id):
        url = f'{self.api_url}/run'
        response = self.HttpPost(url, {'Content-Type': 'application/json'},
                                 json.dumps(Experiment.query.get(experiment_id).serialization()))
        return RestClient.ResponseToJson(response)

    def Get(self, execution_id):
        url = f'{self.api_url}/{execution_id}/logs'
        response = self.HttpGet(url)
        return RestClient.ResponseToJson(response)
