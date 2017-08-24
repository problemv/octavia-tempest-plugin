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
from tempest.common import credentials_factory as common_creds
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test

from octavia_tempest_plugin import clients
from octavia_tempest_plugin.services.load_balancer.common import waiters

LOG = logging.getLogger(__name__)
CONF = config.CONF


class BasePoolMixin(test.BaseTestCase):

    identity_version = 'v3'
    credential_type = 'identity_admin'

    @classmethod
    def setup_clients(cls):
        super(BasePoolMixin, cls).setup_clients()

        credentials = common_creds.get_configured_admin_credentials(
            cls.credential_type, identity_version=cls.identity_version)

        cls.clients = clients.Manager(credentials)
        cls.pool_client = cls.clients.pool_client

    def create_pool(self, listener_id, lb):
        payload = {"pool": {
            "lb_algorithm": "ROUND_ROBIN",
            "protocol": "HTTP",
            "description": "Pool for Tempest tests",
            "listener_id": listener_id,
            "name": "TEMPEST_TEST_POOL"}
        }

        LOG.info('Creating pool')
        pool = self.pool_client.create_pool(payload)

        # Make sure we responded correctly
        self.assertEqual('PENDING_CREATE', pool['provisioning_status'])
        self.assertEqual(True, pool['admin_state_up'])

        # Wait for listener to become active
        waiters.wait_for_status(self.pool_client, 'ACTIVE', pool,
                                'provisioning_status')

        pool = self.pool_client.get_pool(pool['id'])
        self.assertEqual('ACTIVE', pool['provisioning_status'])

        self.addCleanup(self.delete_pool, pool, lb)

        # Wait for load balancer to update
        waiters.wait_for_status(self.lb_client, 'ACTIVE', lb,
                                'provisioning_status')
        return pool

    def delete_pool(self, pool, wait_for_lb=None, ignore_errors=None):
        if wait_for_lb:
            waiters.wait_for_status(self.lb_client, 'ACTIVE', wait_for_lb,
                                    'provisioning_status')
        LOG.info('Deleting pool')
        self.pool_client.delete_pool(pool['id'], ignore_errors)
        waiters.wait_for_error(self.pool_client, lib_exc.NotFound, pool)
        self.assertRaises(lib_exc.NotFound, self.li_client.get_listener,
                          pool['id'])
