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

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'curated',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: oneview_ethernet_network
short_description: Manage OneView Ethernet Network resources.
description:
    - Provides an interface to manage Ethernet Network resources. Can create, update, or delete.
version_added: "2.3"
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.1.0"
author: "Camila Balestrin (@balestrinc)"
options:
    state:
        description:
            - Indicates the desired state for the Ethernet Network resource.
              C(present) will ensure data properties are compliant with OneView.
              C(absent) will remove the resource from OneView, if it exists.
              C(default_bandwidth_reset) will reset the network connection template to the default.
        choices: ['present', 'absent', 'default_bandwidth_reset']
    data:
        description:
            - List with Ethernet Network properties.
        required: true
extends_documentation_fragment:
    - oneview
    - oneview.validateetag
'''

EXAMPLES = '''
- name: Ensure that the Ethernet Network is present using the default configuration
  oneview_ethernet_network:
    config: "{{ config_file_path }}"
    state: present
    data:
      name: 'Test Ethernet Network'
      vlanId: '201'

- name: Update the Ethernet Network changing bandwidth and purpose
  oneview_ethernet_network:
    config: "{{ config_file_path }}"
    state: present
    data:
      name: 'Test Ethernet Network'
      purpose: Management
      bandwidth:
          maximumBandwidth: 3000
          typicalBandwidth: 2000
  delegate_to: localhost

- name: Ensure that the Ethernet Network is present with name 'Renamed Ethernet Network'
  oneview_ethernet_network:
    config: "{{ config_file_path }}"
    state: present
    data:
      name: 'Test Ethernet Network'
      newName: 'Renamed Ethernet Network'

- name: Ensure that the Ethernet Network is absent
  oneview_ethernet_network:
    config: "{{ config_file_path }}"
    state: absent
    data:
      name: 'New Ethernet Network'

- name: Create Ethernet networks in bulk
  oneview_ethernet_network:
    config: "{{ config_file_path }}"
    state: present
    data:
      vlanIdRange: '1-10,15,17'
      purpose: General
      namePrefix: TestNetwork
      smartLink: false
      privateNetwork: false
      bandwidth:
        maximumBandwidth: 10000
        typicalBandwidth: 2000

- name: Reset to the default network connection template
  oneview_ethernet_network:
    config: "{{ config_file_path }}"
    state: default_bandwidth_reset
    data:
      name: 'Test Ethernet Network'
  delegate_to: localhost
'''

RETURN = '''
ethernet_network:
    description: Has the facts about the Ethernet Networks.
    returned: On state 'present'. Can be null.
    type: complex

ethernet_network_bulk:
    description: Has the facts about the Ethernet Networks affected by the bulk insert.
    returned: When 'vlanIdRange' attribute is in data argument. Can be null.
    type: complex

ethernet_network_connection_template:
    description: Has the facts about the Ethernet Network Connection Template.
    returned: On state 'default_bandwidth_reset'. Can be null.
    type: complex
'''

from ansible.module_utils.basic import AnsibleModule
from module_utils.oneview import OneViewModuleBase, ResourceComparator, HPOneViewResourceNotFound


class EthernetNetworkModule(OneViewModuleBase):
    MSG_CREATED = 'Ethernet Network created successfully.'
    MSG_UPDATED = 'Ethernet Network updated successfully.'
    MSG_DELETED = 'Ethernet Network deleted successfully.'
    MSG_ALREADY_EXIST = 'Ethernet Network already exists.'
    MSG_ALREADY_ABSENT = 'Ethernet Network is already absent.'

    MSG_BULK_CREATED = 'Ethernet Networks created successfully.'
    MSG_MISSING_BULK_CREATED = 'Some missing Ethernet Networks were created successfully.'
    MSG_BULK_ALREADY_EXIST = 'The specified Ethernet Networks already exist.'
    MSG_CONNECTION_TEMPLATE_RESET = 'Ethernet Network connection template was reset to the default.'
    MSG_ETHERNET_NETWORK_NOT_FOUND = 'Ethernet Network was not found.'

    RESOURCE_FACT_NAME = 'ethernet_network'

    def __init__(self):

        argument_spec = dict(
            state=dict(
                required=True,
                choices=['present', 'absent', 'default_bandwidth_reset']
            ),
            data=dict(required=True, type='dict'),
        )

        super(EthernetNetworkModule, self).__init__(additional_arg_spec=argument_spec, validate_etag_support=True)

        self.resource_client = self.oneview_client.ethernet_networks

    def execute_module(self):

        changed, msg, ansible_facts, resource = False, '', {}, None

        if self.data.get('name'):
            resource = self.get_by_name(self.data['name'])

        if self.state == 'present':
            if self.data.get('vlanIdRange'):
                changed, msg, ansible_facts = self.__bulk_present()
            else:
                return self.__present(resource)
        elif self.state == 'absent':
            return self.resource_absent(resource)
        elif self.state == 'default_bandwidth_reset':
            changed, msg, ansible_facts = self.__default_bandwidth_reset(resource)

        return dict(changed=changed, msg=msg, ansible_facts=ansible_facts)

    def __present(self, resource):

        bandwidth = self.data.pop('bandwidth', None)
        result = self.resource_present(resource, self.RESOURCE_FACT_NAME)

        if bandwidth:
            if self.__update_connection_template(result['ansible_facts']['ethernet_network'], bandwidth)[0]:
                if not result['changed']:
                    result['changed'] = True
                    result['msg'] = self.MSG_UPDATED

        return result

    def __bulk_present(self):
        vlan_id_range = self.data['vlanIdRange']

        ethernet_networks = self.resource_client.get_range(self.data['namePrefix'], vlan_id_range)

        if not ethernet_networks:
            ethernet_networks = self.resource_client.create_bulk(self.data)
            changed = True
            msg = self.MSG_BULK_CREATED

        else:
            vlan_ids = self.resource_client.dissociate_values_or_ranges(vlan_id_range)
            for net in ethernet_networks[:]:
                vlan_ids.remove(net['vlanId'])

            if len(vlan_ids) == 0:
                msg = self.MSG_BULK_ALREADY_EXIST
                changed = False
            else:
                if len(vlan_ids) == 1:
                    self.data['vlanIdRange'] = '{0}-{1}'.format(vlan_ids[0], vlan_ids[0])
                else:
                    self.data['vlanIdRange'] = ','.join(map(str, vlan_ids))

                self.resource_client.create_bulk(self.data)
                ethernet_networks = self.resource_client.get_range(self.data['namePrefix'], vlan_id_range)
                changed = True
                msg = self.MSG_MISSING_BULK_CREATED

        return changed, msg, dict(ethernet_network_bulk=ethernet_networks)

    def __update_connection_template(self, ethernet_network, bandwidth):

        if 'connectionTemplateUri' not in ethernet_network:
            return False, None

        connection_template = self.oneview_client.connection_templates.get(ethernet_network['connectionTemplateUri'])

        merged_data = connection_template.copy()
        merged_data.update({'bandwidth': bandwidth})

        if not ResourceComparator.compare(connection_template, merged_data):
            connection_template = self.oneview_client.connection_templates.update(merged_data)
            return True, connection_template
        else:
            return False, None

    def __default_bandwidth_reset(self, resource):

        if not resource:
            raise HPOneViewResourceNotFound(self.MSG_ETHERNET_NETWORK_NOT_FOUND)

        default_connection_template = self.oneview_client.connection_templates.get_default()

        changed, connection_template = self.__update_connection_template(resource,
                                                                         default_connection_template['bandwidth'])

        return changed, self.MSG_CONNECTION_TEMPLATE_RESET, dict(
            ethernet_network_connection_template=connection_template)


def main():
    EthernetNetworkModule().run()


if __name__ == '__main__':
    main()
