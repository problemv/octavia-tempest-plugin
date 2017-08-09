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


class BaseListenerTest(test.BaseTestCase):

    identity_version = 'v3'
    credential_type = 'identity_admin'

    @classmethod
    def setup_clients(cls):
        super(BaseListenerTest, cls).setup_clients()

        credentials = common_creds.get_configured_admin_credentials(
            cls.credential_type, identity_version=cls.identity_version)

        cls.clients = clients.Manager(credentials)
        cls.li_client = cls.clients.li_client

    def create_listener(self, lb_id):
        payload = {'listener': {
            'protocol': 'HTTP',
            'description': 'Listener for tempest tests',
            'admin_state_up': True,
            'connection_limit': 200,
            'protocol_port': '80',
            'loadbalancer_id': lb_id,
            'name': 'TEMPEST_TEST_LISTENER'}
        }
        LOG.info('Creating listener')
        listener = self.li_client.create_listener(payload)

        # Make sure we responded correctly
        self.assertEqual('PENDING_CREATE', listener['provisioning_status'])
        self.assertEqual(True, listener['admin_state_up'])

        # Wait for listener to become active
        waiters.wait_for_status(self.li_client, 'ACTIVE', listener,
                                'provisioning_status')

        listener = self.li_client.get_listener(listener['id'])
        self.assertEqual('ACTIVE', listener['provisioning_status'])

        return listener

    def delete_listener(self, li_id, ignore_errors=None):
        listener = self.li_client.get_listener(li_id)
        LOG.info('Deleting listener')
        self.li_client.delete_listener(li_id, ignore_errors)
        waiters.wait_for_error(self.li_client, lib_exc.NotFound, listener)
        self.assertRaises(lib_exc.NotFound, self.li_client.get_listener, li_id)
