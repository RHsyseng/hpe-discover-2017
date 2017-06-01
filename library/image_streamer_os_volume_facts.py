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
module: image_streamer_os_volume_facts
short_description: Retrieve facts about the Image Streamer OS Volumes.
description:
    - Retrieve facts about the Image Streamer OS Volumes.
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.0.1"
author:
    - "Mariana Kreisig (@marikrg)"
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional. If the filepath is not provided, the configuration will be loaded from
          environment variables.
      required: false
    name:
      description:
        - Name of the OS Volume.
      required: false
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           'start': The first item to return, using 0-based indexing.
           'count': The number of resources to return.
           'filter': A general filter/query string to narrow the list of items returned.
           'sort': The sort order of the returned data set."
      required: false
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
    - "Check how to use environment variables for configuration at:
       https://github.com/HewlettPackard/oneview-ansible#environment-variables"
'''

EXAMPLES = '''
- name: Gather facts about all OS Volumes
  image_streamer_os_volume_facts:
    config: "{{ config }}"
  delegate_to: localhost

- debug: var=os_volumes

- name: Gather paginated, filtered and sorted facts about OS Volumes
  image_streamer_os_volume_facts:
    config: "{{ config }}"
    params:
      start: 0
      count: 3
      sort: name:ascending
      filter: status=OK
  delegate_to: localhost

- debug: var=os_volumes

- name: Gather facts about an OS Volume by name
  image_streamer_os_volume_facts:
    config: "{{ config_path }}"
    name: "Test Volume"
  delegate_to: localhost

- debug: var=os_volumes
'''

RETURN = '''
os_volumes:
    description: The list of OS Volumes
    returned: Always, but can be empty.
    type: list
'''
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class OsVolumeFactsModule(object):
    argument_spec = dict(
        config=dict(required=False, type='str'),
        name=dict(required=False, type='str'),
        params=dict(required=False, type='dict')
    )

    def __init__(self):
        self.module = AnsibleModule(argument_spec=self.argument_spec, supports_check_mode=False)
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=HPE_ONEVIEW_SDK_REQUIRED)

        if not self.module.params['config']:
            oneview_client = OneViewClient.from_environment_variables()
        else:
            oneview_client = OneViewClient.from_json_file(self.module.params['config'])

        self.i3s_client = oneview_client.create_image_streamer_client()

    def run(self):
        try:
            name = self.module.params.get("name")

            if name:
                os_volumes = self.i3s_client.os_volumes.get_by('name', name)
            else:
                params = self.module.params.get('params') or {}
                os_volumes = self.i3s_client.os_volumes.get_all(**params)

            self.module.exit_json(changed=False, ansible_facts=dict(os_volumes=os_volumes))

        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))


def main():
    OsVolumeFactsModule().run()


if __name__ == '__main__':
    main()
