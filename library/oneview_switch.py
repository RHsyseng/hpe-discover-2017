#!/usr/bin/python

###
# Copyright (2016) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from ansible.module_utils.basic import *
try:
    from hpOneView.oneview_client import OneViewClient
    from hpOneView.exceptions import HPOneViewException

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: oneview_switch
short_description: Provides an interface to remove ToR Switch resources.
description:
    - "Provides an interface to remove Top of Rack(ToR) Switch resources.
     The switch resource will be removed if it is in an unmanaged state.
     If the switch resource is associated with a Logical Switch, it's removal is treated as a hardware removal only.
     A reference to the switch is mantained, and the resource is marked as 'Absent'."
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.0.0"
author: "Bruno Souza (@bsouza)"
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional. If the file path is not provided, the configuration will be loaded from
          environment variables.
      required: false
    state:
        description:
            - Indicates the desired state for the Switch.
              'absent' will remove the resource from OneView, if it exists.
              'ports_updated' will update the switch ports.
        choices: ['absent', 'ports_updated']
    name:
      description:
        - Switch name.
      required: True
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
    - "Check how to use environment variables for configuration at:
       https://github.com/HewlettPackard/oneview-ansible#environment-variables"
    - This resource is only available on C7000 enclosures
'''

EXAMPLES = '''
- name: Delete the Switch
  oneview_switch:
    config: "{{ config }}"
    state: absent
    name: "172.18.16.2"
'''

SWITCH_DELETED = 'Switch deleted successfully.'
SWITCH_PORTS_UPDATED = "Switch ports updated successfully."
SWITCH_ALREADY_ABSENT = 'Nothing to do.'
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class SwitchModule(object):

    argument_spec = dict(
        config=dict(required=False, type='str'),
        state=dict(
            required=True,
            choices=['absent', 'ports_updated']
        ),
        name=dict(required=True, type='str'),
        data=dict(required=False, type='list')
    )

    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=HPE_ONEVIEW_SDK_REQUIRED)

        if not self.module.params['config']:
            oneview_client = OneViewClient.from_environment_variables()
        else:
            oneview_client = OneViewClient.from_json_file(self.module.params['config'])

        self.resource_client = oneview_client.switches

    def run(self):
        try:
            name = self.module.params["name"]
            state = self.module.params["state"]

            resource = self.__get_by_name(name)

            if state == 'absent':
                changed, msg = self.__delete(resource)
            else:
                changed, msg = self.__update_ports(resource)

            self.module.exit_json(changed=changed, msg=msg)
        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def __get_by_name(self, name):
        result = self.resource_client.get_by('name', name) or [None]
        return result[0]

    def __delete(self, resource):
        if resource:
            self.resource_client.delete(resource)
            return True, SWITCH_DELETED
        else:
            return False, SWITCH_ALREADY_ABSENT

    def __update_ports(self, resource):
        self.resource_client.update_ports(id_or_uri=resource["uri"], ports=self.module.params["data"])
        return True, SWITCH_PORTS_UPDATED


def main():
    SwitchModule().run()


if __name__ == '__main__':
    main()
