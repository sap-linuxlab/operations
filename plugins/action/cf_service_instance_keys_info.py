# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-only
# SPDX-FileCopyrightText: 2024 Red Hat, Project Atmosphere
#
# Copyright 2024 Red Hat, Project Atmosphere
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
import tempfile
from ansible.errors import AnsibleActionFail

__metaclass__ = type
import json
from ansible.plugins.action import ActionBase

from ansible_collections.sap.sap_operations.plugins.action.cf_marketplace_info import (
    CFClient,
)


def run_action(
    client: CFClient,
    service_instance_name: str,
    service_instance_guid: str,
    key_name: str,
    key_guid: str,
) -> dict:

    rc = client.authenticate()
    if rc.get("failed"):
        return rc

    rc, stdout, stderr = client.run_method(
        path="/v3/service_instances",
        method="GET",
        headers={},
        data={},
    )

    if rc or stderr:
        return {"failed": True, "msg": stdout}

    service_instances = json.loads(stdout)

    if "errors" in service_instances:
        return {
            "failed": True,
            "msg": "Error retrieving service instances",
            "errors": service_instances["errors"],
        }
    service_instance = None

    for si in service_instances["resources"]:
        if service_instance_name and si["name"] == service_instance_name:
            service_instance = si

        if service_instance_guid and si["guid"] == service_instance_guid:
            service_instance = si

    if not service_instance:
        return {
            "failed": True,
            "msg": "Service instance not found",
        }

    service_instance_guid = service_instance["guid"]

    rc, stdout, stderr = client.run_method(
        path=f"/v2/service_instances/{service_instance_guid}/service_keys",
        method="GET",
        headers={},
        data={},
    )

    if rc or stderr:
        return {"failed": True, "msg": stdout}

    service_instance_keys = json.loads(stdout)

    if "errors" in service_instance_keys:
        return {
            "failed": True,
            "msg": "Error retrieving service instance keys",
            "errors": service_instance_keys["errors"],
        }

    return dict(
        failed=False,
        changed=False,
        cf_service_instance_keys_info=service_instance_keys["resources"],
    )


class CFServiceInstanceKeysInfoModule(ActionBase):
    _VALID_ARGS = frozenset(["username", "password", "api_endpoint"])
    argument_spec = dict(
        username=dict(type="str", required=False),
        password=dict(type="str", required=False),
        api_endpoint=dict(type="str", required=False),
        service_instance_name=dict(type="str", required=False),
        service_instance_guid=dict(type="str", required=False),
        key_name=dict(
            type="str", required=False, aliases=["service_instance_key_name"]
        ),
        key_guid=dict(
            type="str", required=False, aliases=["service_instance_key_guid"]
        ),
    )
    required_together = [
        [
            "username",
            "password",
            "api_endpoint",
        ],
    ]
    mutually_exclusive = [
        ["service_instance_name", "service_instance_guid"],
        ["key_name", "key_guid"],
    ]
    required_one_of = [
        [
            "username",
            "password",
            "api_endpoint",
        ],
        ["service_instance_name", "service_instance_guid"],
    ]

    def __init__(
        self, task, connection, play_context, loader, templar, shared_loader_obj
    ):
        """Initialize action module."""
        super().__init__(
            task, connection, play_context, loader, templar, shared_loader_obj
        )

    def run(self, tmp=None, task_vars=None):
        validation_results, _ignore = self.validate_argument_spec(
            argument_spec=self.argument_spec,
            required_together=self.required_together,
            mutually_exclusive=self.mutually_exclusive,
            required_one_of=self.required_one_of,
        )

        if validation_results.error_messages:
            raise AnsibleActionFail(
                message="Validation failed: {0}".format(
                    ", ".join(validation_results.error_messages)
                ),
            )
        api_endpoint = self._task.args.get("api_endpoint")
        username = self._task.args.get("username")
        password = self._task.args.get("password")
        service_instance_name = self._task.args.get("service_instance_name")
        service_instance_guid = self._task.args.get("service_instance_guid")
        key_name = self._task.args.get("key_name")
        key_guid = self._task.args.get("key_guid")

        with tempfile.TemporaryDirectory() as cf_home:
            client = CFClient(
                api_endpoint=api_endpoint,
                username=username,
                password=password,
                cf_home=cf_home,
            )
            return run_action(
                client,
                service_instance_name=service_instance_name,
                service_instance_guid=service_instance_guid,
                key_name=key_name,
                key_guid=key_guid,
            )


class ActionModule(CFServiceInstanceKeysInfoModule):
    pass
