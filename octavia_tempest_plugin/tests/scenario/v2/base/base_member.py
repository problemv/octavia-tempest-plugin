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
import time

from oslo_log import log as logging
from six.moves.urllib import error
from six.moves.urllib import request as urllib2
from tempest.common import credentials_factory as common_creds
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test

from octavia_tempest_plugin import clients
from octavia_tempest_plugin.services.load_balancer.common import waiters

LOG = logging.getLogger(__name__)
CONF = config.CONF


class BaseMemberMixin(test.BaseTestCase):

    identity_version = 'v3'
    credential_type = 'identity_admin'

    @classmethod
    def setup_clients(cls):
        super(BaseMemberMixin, cls).setup_clients()

        credentials = common_creds.get_configured_admin_credentials(
            cls.credential_type, identity_version=cls.identity_version)

        cls.clients = clients.Manager(credentials)
        cls.member_client = cls.clients.member_client

    def create_member(self, pool_id, port, address, name, lb):
        payload = {"member": {
            "name": name,
            "weight": "20",
            "address": address,
            "protocol_port": port}
        }

        LOG.info('Creating member')
        member = self.member_client.create_member(pool_id, payload)

        # Make sure we responded correctly
        self.assertEqual('PENDING_CREATE', member['provisioning_status'])
        self.assertEqual(True, member['admin_state_up'])

        # Wait for member to become active
        waiters.wait_for_status(self.member_client, 'ACTIVE', member,
                                'provisioning_status')

        member = self.member_client.get_member(pool_id, member['id'])
        self.assertEqual('ACTIVE', member['provisioning_status'])

        self.addCleanup(self.delete_member, pool_id,
                        member['id'], lb, lib_exc.NotFound)

        return member

    def delete_member(self, pool_id, member_id, wait_for_lb=None,
                      ignore_errors=None):
        if wait_for_lb:
            waiters.wait_for_status(self.lb_client, 'ACTIVE', wait_for_lb,
                                    'provisioning_status')
        member = self.member_client.get_member(pool_id=pool_id,
                                               member_id=member_id)
        LOG.info('Deleting member')
        self.member_client.delete_member(pool_id, member_id, ignore_errors)
        waiters.wait_for_error(self.pool_client, lib_exc.NotFound, member)
        self.assertRaises(lib_exc.NotFound, self.li_client.get_listener,
                          pool_id)

    @staticmethod
    def check_round_robin(lb, members):
        def try_connect(check_ip, port):
            responses = []
            try:
                for name in members:
                    LOG.info('checking connection to ip: %s port: %d',
                             check_ip, port)
                    resp = urllib2.urlopen("http://{0}:{1}/".format(check_ip,
                                                                    port))
                    responses.append(resp.read().rstrip())
                if sorted(responses) == sorted(members.keys()):
                    return True
                return False
            except IOError as e:
                LOG.info('Got IOError in check connection: %s', e)
                return False
            except error.HTTPError as e:
                LOG.info('Got HTTPError in check connection: %s', e)
                return False

        timeout = CONF.validation.ping_timeout
        start = time.time()
        while not try_connect(lb['vip_address'], 80):
            if (time.time() - start) > timeout:
                message = "Timed out trying to connect to {}".format(
                    lb['vip_address'])
                raise lib_exc.TimeoutException(message)
            time.sleep(1)
