#   Copyright 2017 GoDaddy
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import json


from tempest import config
from tempest.lib.common import rest_client

CONF = config.CONF


class HealthMonitorClient(rest_client.RestClient):

    _uri = '/v2.0/lbaas/healthmonitors'

    def __init__(self, auth_provider, service, region):
        super(HealthMonitorClient, self).__init__(auth_provider, service,
                                                  region)
        self.timeout = CONF.octavia_tempest.build_timeout
        self.build_interval = CONF.octavia_tempest.build_interval
        self.resource_name = 'health monitor'

    def list_health_monitors(self):
        response, body = self.get(self._uri)
        self.expected_success(200, response.status)
        return json.loads(body)

    def create_health_monitor(self, payload):
        response, body = self.post(self._uri, json.dumps(payload))
        self.expected_success(201, response.status)
        return json.loads(body)['healthmonitor']

    def delete_health_monitor(self, healthmonitor_id, ignore_errors=None):
        uri = self._uri + '/{}'.format(healthmonitor_id)
        if ignore_errors:
            try:
                response, body = self.delete(uri)
            except ignore_errors:
                return
        else:
            response, body = self.delete(uri)

        self.expected_success(204, response.status)
        return response.status

    def get_health_monitor(self, healthmonitor_id):
        uri = self._uri + '/{}'.format(healthmonitor_id)

        response, body = self.get(uri)
        self.expected_success(200, response.status)
        return json.loads(body)['healthmonitor']

    def update_health_monitor(self, healthmonitor_id, payload):
        uri = self._uri + '/{}'.format(healthmonitor_id)
        response, body = self.put(uri, json.dumps(payload))
        self.expected_success(200, response.status)
        return json.loads(body)['healthmonitor']

    def get_status(self, healthmonitor):
        return self.get_health_monitor(healthmonitor['id'])
