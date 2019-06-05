import json
from typing import Dict
from app.models import Experiment
from .restClient import RestClient


class DispatcherApi(RestClient):

    def __init__(self, api_host, api_port, suffix):
        super().__init__(api_host, api_port, suffix)

    def Post(self, experimentId: int) -> Dict:
        url = f'{self.api_url}/run'
        response = self.HttpPost(url, {'Content-Type': 'application/json'},
                                 json.dumps(Experiment.query.get(experimentId).serialization()))
        return RestClient.ResponseToJson(response)

    def Get(self, executionId: int) -> Dict:
        url = f'{self.api_url}/{executionId}/logs'
        response = self.HttpGet(url)
        return RestClient.ResponseToJson(response)
