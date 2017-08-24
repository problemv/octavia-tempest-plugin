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

from oslo_log import log as logging
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test

from octavia_tempest_plugin.services.load_balancer.common import waiters

LOG = logging.getLogger(__name__)
CONF = config.CONF


class BaseHealthMonitorMixin(test.BaseTestCase):

    def create_health_monitor(self, pool, lb):
        payload = {"healthmonitor": {
            "name": "TEMPEST_TEST_HM",
            "admin_state_up": True,
            "pool_id": pool['id'],
            "delay": "10",
            "expected_codes": "200",
            "max_retries": "1",
            "http_method": "GET",
            "timeout": "5",
            "url_path": "/",
            "type": "HTTP",
            "max_retries_down": 3}
        }
        LOG.info('Creating health monitor')
        health_monitor = self.hm_client.create_health_monitor(payload)

        # Make sure we responded correctly
        self.assertEqual('PENDING_CREATE',
                         health_monitor['provisioning_status'])
        self.assertEqual(True, health_monitor['admin_state_up'])

        # Wait for health monitor to become active
        waiters.wait_for_status(self.hm_client, 'ACTIVE', health_monitor,
                                'provisioning_status')

        health_monitor = self.hm_client.get_health_monitor(
            health_monitor['id'])
        self.assertEqual('ACTIVE', health_monitor['provisioning_status'])

        self.addCleanup(self.delete_health_monitor, health_monitor, lb)

        # Wait for load balancer to update
        waiters.wait_for_status(self.lb_client, 'ACTIVE', lb,
                                'provisioning_status')

        return health_monitor

    def delete_health_monitor(self, health_monitor, wait_for_lb=None,
                              ignore_errors=None):
        if wait_for_lb:
            waiters.wait_for_status(self.lb_client, 'ACTIVE', wait_for_lb,
                                    'provisioning_status')
        health_monitor = self.hm_client.get_health_monitor(
            health_monitor['id'])

        LOG.info('Deleting health monitor')
        self.hm_client.delete_health_monitor(health_monitor['id'],
                                             ignore_errors)
        waiters.wait_for_error(self.hm_client, lib_exc.NotFound,
                               health_monitor)

        self.assertRaises(lib_exc.NotFound, self.li_client.get_listener,
                          health_monitor['id'])
