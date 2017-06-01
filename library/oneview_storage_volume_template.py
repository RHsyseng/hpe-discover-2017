#!/usr/bin/python
# -*- coding: utf-8 -*-
###
# Copyright (2016-2017) Hewlett Packard Enterprise Development LP
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}

DOCUMENTATION = '''
---
module: oneview_storage_volume_template
short_description: Manage OneView Storage Volume Template resources.
description:
    - "Provides an interface to manage Storage Volume Template resources. Can create, update and delete."
version_added: "2.3"
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.1.0"
author: "Gustavo Hennig (@GustavoHennig)"
options:
    state:
        description:
            - Indicates the desired state for the Storage Volume Template resource.
              C(present) will ensure data properties are compliant with OneView.
              C(absent) will remove the resource from OneView, if it exists.
        choices: ['present', 'absent']
        required: true
    data:
        description:
            - List with Storage Volume Template properties and its associated states.
        required: true
extends_documentation_fragment:
    - oneview
    - oneview.validateetag
'''

EXAMPLES = '''
- name: Create a Storage Volume Template
  oneview_storage_volume_template:
    config: "{{ config }}"
    state: present
    data:
        name: 'Volume Template Name'
        state: "Configured"
        description: "Example Template"
        provisioning:
             shareable: true
             provisionType: "Thin"
             capacity: "235834383322"
             storagePoolUri: "/rest/storage-pools/2D69A182-862E-4ECE-8BEE-73E0F5BEC855"
        stateReason: "None"
        storageSystemUri: "/rest/storage-systems/TXQ1010307"
        snapshotPoolUri: "/rest/storage-pools/2D69A182-862E-4ECE-8BEE-73E0F5BEC855"
        type: StorageVolumeTemplateV3
  delegate_to: localhost


- name: Delete the Storage Volume Template
  oneview_storage_volume_template:
    config: "{{ config }}"
    state: absent
    data:
        name: 'Volume Template Name'
  delegate_to: localhost
'''

RETURN = '''
storage_volume_template:
    description: Has the OneView facts about the Storage Volume Template.
    returned: On 'present' state, but can be null.
    type: complex
'''

from ansible.module_utils.basic import AnsibleModule
from module_utils.oneview import OneViewModuleBase, HPOneViewValueError


class StorageVolumeTemplateModule(OneViewModuleBase):
    MSG_CREATED = 'Storage Volume Template created successfully.'
    MSG_UPDATED = 'Storage Volume Template updated successfully.'
    MSG_ALREADY_EXIST = 'Storage Volume Template is already updated.'
    MSG_DELETED = 'Storage Volume Template deleted successfully.'
    MSG_ALREADY_ABSENT = 'Storage Volume Template is already absent.'
    MSG_MANDATORY_FIELD_MISSING = "Mandatory field was not informed: data.name"

    def __init__(self):
        argument_spec = dict(
            state=dict(
                required=True,
                choices=['present', 'absent']
            ),
            data=dict(required=True, type='dict'),
        )
        super(StorageVolumeTemplateModule, self).__init__(additional_arg_spec=argument_spec, validate_etag_support=True)

        self.resource_client = self.oneview_client.storage_volume_templates

    def execute_module(self):

        if not self.data.get('name'):
            raise HPOneViewValueError(self.MSG_MANDATORY_FIELD_MISSING)

        resource = self.get_by_name(self.data['name'])

        if self.state == 'present':
            return self.resource_present(resource, fact_name='storage_volume_template')
        elif self.state == 'absent':
            return self.resource_absent(resource)


def main():
    StorageVolumeTemplateModule().run()


if __name__ == '__main__':
    main()
