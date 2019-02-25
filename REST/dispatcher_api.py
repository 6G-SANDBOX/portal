from .rest_client import RestClient
import json


class Dispatcher_Api(RestClient):

    def __init__(self, api_host, api_port, suffix):
        super().__init__(api_host, api_port, suffix)

    def Post(self, experiment_id, experiment_name, user_id):
        url = f'{self.api_url}/run'
        response = self.HttpPost(url, {'Content-Type': 'application/json'},
                                 json.dumps({'Experiment_id': experiment_id, 'Experiment_name': experiment_name,
                                             'User': user_id}))
        return RestClient.ResponseToJson(response)
