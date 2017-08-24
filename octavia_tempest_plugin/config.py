# Copyright 2016 Rackspace Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from oslo_config import cfg

"""
    For running Octavia tests, it  is assumed that the following option is
    defined in the [service_available] section of etc/tempest.conf
    octavia = True
"""
service_available_group = cfg.OptGroup(name='service_available',
                                       title='Available OpenStack Services')

ServiceAvailableGroup = [
    cfg.BoolOpt('load-balancer',
                default=True,
                help="Whether or not Octavia is expected to be available."),
]

octavia_group = cfg.OptGroup(name='octavia_tempest',
                             title='octavia service options')

OctaviaGroup = [
    cfg.StrOpt('catalog_type',
               default='network',
               help='Catalog type of the Octavia service.'),
    cfg.IntOpt('build_interval',
               default=5,
               help='Time in seconds between build status checks for '
                    'non-load-balancer resources to build'),
    cfg.IntOpt('build_timeout',
               default=30,
               help='Timeout in seconds to wait for non-load-balancer '
                    'resources to build'),
    cfg.IntOpt('lb_build_interval',
               default=15,
               help='Time in seconds between build status checks for a '
                    'load balancer.'),
    cfg.IntOpt('lb_build_timeout',
               default=900,
               help='Timeout in seconds to wait for a '
                    'load balancer to build.'),
    cfg.StrOpt('vip_network_id',
               default=None,
               help='Network to provision load balancer from.'),
    cfg.StrOpt('server_network_id',
               default=None,
               help='Network to provision server from.'),
    cfg.IntOpt('ip_version',
               default=4,
               help='IP version to use for member creation (4 or 6).'),
    cfg.ListOpt('image_tags',
                default=None,
                help='Tags to use for to select an image for VM creation.'),
    cfg.StrOpt('availability_zone',
               default=None,
               help='Availability zone to use for server creation.'),
    cfg.IntOpt('random_server_name_length',
               default=15,
               help='Length of the name to use for server creation.'),
]
