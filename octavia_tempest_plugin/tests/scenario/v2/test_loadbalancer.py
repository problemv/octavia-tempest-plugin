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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest import test

from octavia_tempest_plugin import clients
from octavia_tempest_plugin.services.load_balancer.common import waiters
from octavia_tempest_plugin.tests.scenario.v2.base import base_listener
from octavia_tempest_plugin.tests.scenario.v2.base import base_loadbalancer

LOG = logging.getLogger(__name__)
CONF = config.CONF


class TestLoadbalancerSmoke(test.BaseTestCase):

    identity_version = 'v3'
    credential_type = 'identity_admin'

    @classmethod
    def setup_clients(cls):
        super(TestLoadbalancerSmoke, cls).setup_clients()

        credentials = common_creds.get_configured_admin_credentials(
            cls.credential_type, identity_version=cls.identity_version)

        cls.clients = clients.Manager(credentials)
        cls.lb_client = cls.clients.lb_client

    @test.services('network', 'image', 'compute')
    @decorators.attr(type='smoke')
    @decorators.attr(type='slow')
    @decorators.idempotent_id('b49ab314-67a6-464e-b7a9-ee156bf1090a')
    def test_crud_loadbalancer(self):
        payload = {'loadbalancer': {
            'vip_network_id': CONF.octavia_tempest.vip_network_id,
            'name': 'TEMPEST_TEST_LB',
            'description': 'LB for Tempest tests'}
        }

        lb = self.lb_client.create_loadbalancer(payload)
        self.addCleanup(self.lb_client.delete_loadbalancer, lb['id'],
                        ignore_errors=lib_exc.Conflict)

        # Make sure we responded correctly
        self.assertEqual('PENDING_CREATE', lb['provisioning_status'])
        self.assertEqual(True, lb['admin_state_up'])

        # Wait for loadbalancer's status to update
        waiters.wait_for_status(self.lb_client, 'ACTIVE', lb,
                                'provisioning_status')

        payload = {'loadbalancer': {
            'name': 'TEMPEST_TEST_LB_UPDATED'}
        }
        lb = self.lb_client.update_loadbalancer(lb['id'], payload)

        waiters.wait_for_status(self.lb_client, 'ACTIVE', lb,
                                'provisioning_status')

        lb = self.lb_client.get_loadbalancer(lb['id'])
        self.assertEqual('ACTIVE', lb['provisioning_status'])
        self.assertEqual('TEMPEST_TEST_LB_UPDATED', lb['name'])

        self.lb_client.delete_loadbalancer(lb['id'])
        waiters.wait_for_status(self.lb_client, 'DELETED', lb,
                                'provisioning_status')
        lb = self.lb_client.get_loadbalancer(lb['id'])
        self.assertEqual('DELETED', lb['provisioning_status'])


class TestOctaviaFull(base_loadbalancer.BaseLoadbalancerTest,
                      base_listener.BaseListenerTest):

    @test.services('network', 'image', 'compute')
    @decorators.attr(type='slow')
    @decorators.idempotent_id('c93e7354-4e4d-4c78-af84-5486688f47cb')
    def test_octavia_full(self):
        # Will be adding parts to this test individually

        # Create load balancer for end to end tests.
        lb = self.create_loadbalancer()
        self.addCleanup(self.lb_client.delete_loadbalancer, lb['id'],
                        lib_exc.Conflict)

        # Create listener for load balancer
        listener = self.create_listener(lb['id'])
        self.addCleanup(self.li_client.delete_listener, listener['id'],
                        lib_exc.NotFound)

        # Wait for load balancer to update
        waiters.wait_for_status(self.lb_client, 'ACTIVE', lb,
                                'provisioning_status')

        # Delete listener
        self.delete_listener(listener['id'])

        # Delete load balancer
        self.delete_loadbalancer(lb['id'])
