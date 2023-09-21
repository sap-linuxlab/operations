#!/usr/bin/python
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: GPL-3.0-only
# SPDX-FileCopyrightText: 2023 Red Hat, Project Atmosphere
#
# Copyright 2023 Red Hat, Project Atmosphere
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: parameter_info

author:
  - Ondra Machacek (@machacekondra)

short_description: Parameter information

description:
  - Fetch the info about profile parameter from SAP via SOAP
version_added: 1.0.0

options:
  username:
    description:
      - "I(username) of the SAP system"
    type: str
  password:
    description:
      - "I(password) of the SAP system"
    type: str
  hostname:
    description:
      - "I(hostname) of the SAP system"
    type: str
  ca_file:
    description:
      - "I(ca_file) use CA certificate to secure the communication. By default system CA store is used."
    type: str
  instance_number:
    description:
      - "I(instance_number) is the instance number to be managed."
    type: str
    required: true
  secure:
    description:
      - "I(secure) specify if secure communication should be enforced."
      - "By default system CA store is used. User can pass custom CA by I(ca_file) parameter."
    choices: [ strict,insecure,none ]
    default: strict
    type: str
  name:
    description:
      - Parameter name to fetch info about.
    type: str
requirements:
  - python >= 3.6
  - suds >= 1.1.2
"""

EXAMPLES = r"""
- name: Use module with local socket on target machine
  sap.sap_operations.parameter_info:
    instance_number: "0"

- name: Fetch values of all parameters
  sap.sap_operations.parameter_info:
    username: "npladm"
    password: "secret123!"
    hostname: "sap.system.example.com"
    instance_number: "0"

- name: Fetch values of DIR_CT_RUN parameter
  sap.sap_operations.parameter_info:
    username: "npladm"
    password: "secret123!"
    hostname: "sap.system.example.com"
    instance_number: "0"
    name: DIR_CT_RUN
"""

RETURN = r"""
parameter_value:
    description: Parameter values
    type: list
    returned: always
    sample: [
        '/usr/sap/NPL/SYS/exe/uc/linuxx86_64'
    ]
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.sap.sap_operations.plugins.module_utils import soap


def soap_client(hostname, username, password, ca_file, secure, instance):
    return soap.SAPClient(hostname, username, password, ca_file, secure, instance)


def main():
    module_args = dict(
        username=dict(type="str"),
        password=dict(type="str", no_log=True),
        hostname=dict(type="str"),
        ca_file=dict(type="str"),
        instance_number=dict(type="str", required=True),
        secure=dict(
            choices=["strict", "insecure", "none"], default="strict", type="str"
        ),
        name=dict(type="str"),
    )

    result = dict(changed=False)
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_together=[["username", "password", "hostname"]],
    )
    soap.check_sdk(module)

    hostname = module.params.get("hostname")
    username = module.params.get("username")
    password = module.params.get("password")
    ca_file = module.params.get("ca_file")
    secure = module.params.get("secure")
    instance_number = module.params.get("instance_number")

    client = soap_client(hostname, username, password, ca_file, secure, instance_number)
    try:
        client.connect()
    except Exception as err:
        module.fail_json(msg=(str(err)))

    result["parameter_value"] = client.parameter_value(module.params.get("name"))

    module.exit_json(**result)


if __name__ == "__main__":
    main()
