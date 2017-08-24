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


class BaseListenerMixin(test.BaseTestCase):

    def create_listener(self, lb):
        payload = {'listener': {
            'protocol': 'HTTP',
            'description': 'Listener for tempest tests',
            'admin_state_up': True,
            'connection_limit': 200,
            'protocol_port': '80',
            'loadbalancer_id': lb['id'],
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

        self.addCleanup(self.delete_listener, listener, lb)

        # Wait for load balancer to update
        waiters.wait_for_status(self.lb_client, 'ACTIVE', lb,
                                'provisioning_status')

        return listener

    def delete_listener(self, listener, wait_for_lb=None, ignore_errors=None):
        if wait_for_lb:
            waiters.wait_for_status(self.lb_client, 'ACTIVE', wait_for_lb,
                                    'provisioning_status')
        listener = self.li_client.get_listener(listener['id'])

        LOG.info('Deleting listener')
        self.li_client.delete_listener(listener['id'], ignore_errors)
        waiters.wait_for_error(self.li_client, lib_exc.NotFound, listener)

        self.assertRaises(lib_exc.NotFound, self.li_client.get_listener,
                          listener['id'])
