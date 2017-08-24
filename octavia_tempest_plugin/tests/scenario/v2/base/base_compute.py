# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import copy
import os

from oslo_log import log as logging
from tempest.common import credentials_factory as common_creds
from tempest.common import waiters
from tempest import config
from tempest.lib.common import ssh
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import test

from octavia_tempest_plugin import clients
from octavia_tempest_plugin.tests.scenario.v2.base import constants as const

CONF = config.CONF

LOG = logging.getLogger(__name__)
HTTPD_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 '../../../contrib/httpd.go'))


class BaseComputeMixin(test.BaseTestCase):

    identity_version = 'v3'
    credential_type = 'identity_admin'

    @classmethod
    def setup_clients(cls):
        super(BaseComputeMixin, cls).setup_clients()

        credentials = common_creds.get_configured_admin_credentials(
            cls.credential_type, identity_version=cls.identity_version)

        cls.clients = clients.Manager(credentials)

    def create_test_server(self, members, network=None, name=None, flavor=None,
                           **kwargs):
        if name is None:
            name = data_utils.rand_name(__name__ + "-instance")
        if flavor is None:
            flavor = CONF.compute.flavor_ref
        if CONF.octavia_tempest.image_tags:
            self.clients.image_client_v2.list_images()
        else:
            image_id = CONF.compute.image_ref

        kwargs = self.set_networks_kwarg(network, kwargs) or {}

        # Create keypair
        servers_keypairs = self.create_keypair()

        secgroup_rules = copy.deepcopy(const.SECURITY_GROUP_RULES)
        secgroup_name, secgroup_id = self.create_secgroup(secgroup_rules)

        # Create test server
        LOG.info('Creating test server: {}'.format(name))
        server = self.clients.servers_client.create_server(
            name=name, imageRef=image_id, flavorRef=flavor,
            key_name=servers_keypairs['name'],
            security_groups=[{'name': secgroup_name}], **kwargs)

        # Wait for server to fully build
        waiters.wait_for_server_status(
            self.clients.servers_client, server['server']['id'], 'ACTIVE')

        # Return fully populated server
        server = self.clients.servers_client.show_server(
            server['server']['id'])

        # Start HTTP backend
        for name, port in members.items():
            self._start_backend_httpd_processes(server, servers_keypairs,
                                                name, port)

        self.addCleanup(self.cleanup_server, server['server']['id'],
                        secgroup_id)
        return server

    def _start_backend_httpd_processes(self, server, keypair, name, port):
        private_key = keypair['private_key']
        username = CONF.validation.image_ssh_user
        ip = self.get_server_ip(server)

        ssh_client = ssh.Client(ip, username, pkey=private_key)

        start_server = ("(while true; do echo -e 'HTTP/1.0 200 OK\r\n\r\n"
                        "{server_name}' | sudo nc -l -p {port} ; "
                        "done)&".format(server_name=name, port=port))
        ssh_client.exec_command(start_server)

    def create_secgroup(self, rule_list):
        # Create security group
        secgroup_name = data_utils.rand_name('security-group')
        LOG.info('Creating security group: {}'.format(secgroup_name))
        secgroup = self.clients.security_groups_client\
            .create_security_group(name=secgroup_name)

        sgs = self.clients.security_groups_client.list_security_groups()
        group_id = None
        for sg in sgs['security_groups']:
            if sg['name'] == secgroup_name:
                group_id = sg['id']
                break

        for i in rule_list:
            direction = i.pop('direction')
            (self.clients.security_group_rules_client.
             create_security_group_rule(direction=direction,
                                        security_group_id=group_id,
                                        **i))
        return secgroup['security_group']['name'], group_id

    def create_keypair(self):
        name = data_utils.rand_name('keypair-test')
        body = self.clients.keypairs_client.create_keypair(name=name)
        return body['keypair']

    def cleanup_server(self, server_id, security_group_id):
        self.clients.servers_client.delete_server(server_id)
        waiters.wait_for_server_termination(
            self.clients.servers_client, server_id)
        # Wait for server to fully delete so security group delete doesnt fail
        try:
            self.clients.security_groups_client.delete_security_group(
                security_group_id)
        except lib_exc.NotFound:
            pass

    @staticmethod
    def set_networks_kwarg(network, kwargs=None):
        params = copy.copy(kwargs) or {}
        if kwargs and 'networks' in kwargs:
            return params

        if network:
            if 'id' in network.keys():
                params.update({"networks": [{'uuid': network['id']}]})
            else:
                LOG.warning('The provided network dict: %s was invalid and '
                            'did not contain an id', network)
        return params

    @staticmethod
    def get_server_ip(server):
        addresses = server['server']['addresses'].values()[0]
        for i in addresses:
            if i['version'] == CONF.octavia_tempest.ip_version:
                return i['addr']
        else:
            raise lib_exc.NotFound('Unable to find an IP address for test '
                                   'server.')
