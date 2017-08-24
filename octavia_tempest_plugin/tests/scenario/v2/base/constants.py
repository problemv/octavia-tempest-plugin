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

SECURITY_GROUP_RULES = [
    {"direction": "ingress",
     "port_range_min": "80",
     "ethertype": "IPv4",
     "port_range_max": "80",
     "protocol": "tcp",
     'remote_ip_prefix': '0.0.0.0/0'},
    {"direction": "ingress",
     "port_range_min": "81",
     "ethertype": "IPv4",
     "port_range_max": "81",
     "protocol": "tcp",
     'remote_ip_prefix': '0.0.0.0/0'},
    {"direction": "ingress",
     "port_range_min": "22",
     "ethertype": "IPv4",
     "port_range_max": "22",
     "protocol": "tcp",
     'remote_ip_prefix': '0.0.0.0/0'},
    {"direction": "ingress",
     "ethertype": "IPv4",
     'protocol': 'icmp',
     'remote_ip_prefix': '0.0.0.0/0'}]

MEMBER_CONFIG = {"Tempest-Member1": 80,
                 "Tempest-Member2": 81}
