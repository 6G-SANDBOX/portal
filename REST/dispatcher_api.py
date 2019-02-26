from .rest_client import RestClient
from app.models import Experiment

import json


class Dispatcher_Api(RestClient):

    def __init__(self, api_host, api_port, suffix):
        super().__init__(api_host, api_port, suffix)

    def Post(self, experiment_id, experiment_name, user_id):
        url = f'{self.api_url}/run'
        response = self.HttpPost(url, {'Content-Type': 'application/json'},
                                 json.dumps(Experiment.query.get(experiment_id).serialization()))
        return RestClient.ResponseToJson(response)
