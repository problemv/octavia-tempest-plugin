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
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
LOG = logging.getLogger(__name__)


def wait_for_status(client, status, resource, status_key):
    start = int(time.time())
    LOG.info('Waiting for {name} status to update to {status}'.format(
        name=client.resource_name, status=status))
    while True:
        response = client.get_status(resource)
        if response[status_key] != status:
            time.sleep(client.build_interval)
        elif response[status_key] == status:
            LOG.info('{name}\'s status updated to {status}.'.format(
                name=client.resource_name, status=status))
            return
        elif response[status_key] == 'ERROR':
            message = '{name} updated to an invalid state of ERROR'.format(
                name=client.resource_name)
            raise lib_exc.CommandFailed(message)
        elif int(time.time()) - start >= client.timeout:
            message = (
                '{name} failed to update within the required time '
                '{timeout}. Current status of {name}: {status}'.format(
                    name=client.resource_name,
                    timeout=client.timeout,
                    status=response[status_key]
                ))
            caller = test_utils.find_test_caller()

            if caller:
                message = '({caller}) {message}'.format(caller=caller,
                                                        message=message)

            raise lib_exc.TimeoutException(message)


def wait_for_error(client, error, resource):
    start = int(time.time())
    LOG.info('Waiting for {name} to error'.format(name=client.resource_name))
    try:
        while True:
            response = client.get_status(resource)
            if int(time.time()) - start >= client.timeout:
                message = (
                    '{name} failed to error within the required time '
                    '{timeout}. Response: {response}'.format(
                        name=client.resource_name,
                        timeout=client.timeout,
                        response=response
                    ))
                caller = test_utils.find_test_caller()

                if caller:
                    message = '({caller}) {message}'.format(caller=caller,
                                                            message=message)

                raise lib_exc.TimeoutException(message)
    except error:
        LOG.info('{name} errored successfully'.format(
            name=client.resource_name))
