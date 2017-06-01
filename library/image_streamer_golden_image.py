#!/usr/bin/python
# -*- coding: utf-8 -*-
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
    from hpOneView.extras.comparators import resource_compare
    from hpOneView.exceptions import HPOneViewException
    from hpOneView.exceptions import HPOneViewResourceNotFound
    from hpOneView.exceptions import HPOneViewValueError

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: image_streamer_golden_image
short_description: Manage Image Streamer Golden Image resources.
description:
    - "Provides an interface to manage Image Streamer Golden Image. Can create, add, update, and remove."
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.1.0"
author: "Gustavo Hennig (@GustavoHennig)"
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional. If the file path is not provided, the configuration will be loaded from
          environment variables.
      required: false
    state:
        description:
            - Indicates the desired state for the Golden Image resource.
              'present' will ensure data properties are compliant with OneView.
              'absent' will remove the resource from OneView, if it exists.
              'downloaded' will download the Golden Image to the file path provided.
              'archive_downloaded' will download the Golden Image archive to the file path provided.
        choices: ['present', 'absent', 'downloaded', 'archive_downloaded']
        required: true
    data:
        description:
            - List with Golden Image properties and its associated states.
        required: true
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
    - "Check how to use environment variables for configuration at:
       https://github.com/HewlettPackard/oneview-ansible#environment-variables"
    - This resource is only available on HPE Synergy
'''

EXAMPLES = '''
- name: Add a Golden Image from OS Volume
  image_streamer_golden_image:
    config: "{{ config }}"
    state: present
    data:
      name: 'Demo Golden Image creation'
      description: "Test Description"
      imageCapture: "true"
      osVolumeName: 'OSVolume-20'
      buildPlanName: 'Buld Plan name'
  delegate_to: localhost

- name: Create a Golden Image uploading from a local file
  image_streamer_golden_image:
    config: "{{ config }}"
    state: present
    data:
      name: 'Demo Golden Image upload'
      description: "Test"
      localImageFilePath: '~/image_file.zip'
  delegate_to: localhost

- name: Update the Golden Image description and name
  image_streamer_golden_image:
    config: "{{ config }}"
    state: present
    data:
      name: 'Demo Golden Image upload'
      description: "New description"
      newName: 'Golden Image Renamed'
  delegate_to: localhost

- name: Download the Golden Image to the file path provided
  image_streamer_golden_image:
    config: "{{ config }}"
    state: downloaded
    data:
      name: 'Demo Golden Image'
      destination_file_path: '~/downloaded_image.zip'
  delegate_to: localhost

- name: Download the Golden Image archive log to the file path provided
  image_streamer_golden_image:
    config: "{{ config }}"
    state: archive_downloaded
    data:
      name: 'Demo Golden Image'
      destination_file_path: '~/archive.log'
  delegate_to: localhost

- name: Remove a Golden Image
  image_streamer_golden_image:
    config: "{{ config }}"
    state: absent
    data:
        name: 'Golden Image name'
  delegate_to: localhost
'''

RETURN = '''
golden_image:
    description: Has the OneView facts about the Golden Image.
    returned: On state 'present'.
    type: complex
'''

GOLDEN_IMAGE_CREATED = 'Golden Image created successfully.'
GOLDEN_IMAGE_UPLOADED = 'Golden Image uploaded successfully.'
GOLDEN_IMAGE_UPDATED = 'Golden Image updated successfully.'
GOLDEN_IMAGE_ALREADY_UPDATED = 'Golden Image is already present.'
GOLDEN_IMAGE_DELETED = 'Golden Image deleted successfully.'
GOLDEN_IMAGE_DOWNLOADED = 'Golden Image downloaded successfully.'
GOLDEN_IMAGE_ARCHIVE_DOWNLOADED = 'Golden Image archive downloaded successfully.'
GOLDEN_IMAGE_ALREADY_ABSENT = 'Golden Image is already absent.'
GOLDEN_IMAGE_WAS_NOT_FOUND = 'Golden Image was not found.'
I3S_CANT_CREATE_AND_UPLOAD = "You can use an existent OS Volume or upload an Image, you cannot do both."
I3S_MISSING_MANDATORY_ATTRIBUTES = 'Mandatory field is missing: osVolumeURI or localImageFilePath are required.'
I3S_OS_VOLUME_WAS_NOT_FOUND = 'OS Volume was not found.'
I3S_BUILD_PLAN_WAS_NOT_FOUND = 'OS Build Plan was not found.'
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class GoldenImageModule(object):
    argument_spec = dict(
        config=dict(required=False, type='str'),
        state=dict(
            required=True,
            choices=['present', 'absent', 'downloaded', 'archive_downloaded']
        ),
        data=dict(required=True, type='dict')
    )

    def __init__(self):
        self.module = AnsibleModule(argument_spec=self.argument_spec, supports_check_mode=False)
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=HPE_ONEVIEW_SDK_REQUIRED)

        if not self.module.params['config']:
            self.oneview_client = OneViewClient.from_environment_variables()
        else:
            self.oneview_client = OneViewClient.from_json_file(self.module.params['config'])

        self.i3s_client = self.oneview_client.create_image_streamer_client()

    def run(self):
        try:
            state = self.module.params['state']
            data = self.module.params['data']
            changed, msg, ansible_facts = False, '', {}

            resource = (self.i3s_client.golden_images.get_by("name", data['name']) or [None])[0]

            if state == 'present':
                changed, msg, ansible_facts = self.__present(data, resource)
            elif state == 'absent':
                changed, msg, ansible_facts = self.__absent(resource)
            else:
                if not resource:
                    raise HPOneViewResourceNotFound(GOLDEN_IMAGE_WAS_NOT_FOUND)

                if state == 'downloaded':
                    changed, msg, ansible_facts = self.__download(data, resource)
                elif state == 'archive_downloaded':
                    changed, msg, ansible_facts = self.__download_archive(data, resource)

            self.module.exit_json(changed=changed,
                                  msg=msg,
                                  ansible_facts=ansible_facts)

        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def __check_present_consistency(self, data):
        if data.get('osVolumeURI') and data.get('localImageFilePath'):
            raise HPOneViewValueError(I3S_CANT_CREATE_AND_UPLOAD)

    def __present(self, data, resource):

        changed = False
        msg = ''

        if "newName" in data:
            data["name"] = data.pop("newName")

        self.__replace_name_by_uris(data)
        self.__check_present_consistency(data)

        file_path = data.pop('localImageFilePath', None)

        if not resource:
            if data.get('osVolumeURI'):
                resource = self.i3s_client.golden_images.create(data)
                msg = GOLDEN_IMAGE_CREATED
                changed = True
            elif file_path:
                resource = self.i3s_client.golden_images.upload(file_path, data)
                msg = GOLDEN_IMAGE_UPLOADED
                changed = True
            else:
                raise HPOneViewValueError(I3S_MISSING_MANDATORY_ATTRIBUTES)
        else:
            merged_data = resource.copy()
            merged_data.update(data)

            if not resource_compare(resource, merged_data):
                # update resource
                resource = self.i3s_client.golden_images.update(merged_data)
                changed = True
                msg = GOLDEN_IMAGE_UPDATED
            else:
                msg = GOLDEN_IMAGE_ALREADY_UPDATED

        return changed, msg, dict(golden_image=resource)

    def __replace_name_by_uris(self, data):
        vol_name = data.pop('osVolumeName', None)
        if vol_name:
            data['osVolumeURI'] = self.__get_os_voume_by_name(vol_name)['uri']

        build_plan_name = data.pop('buildPlanName', None)
        if build_plan_name:
            data['buildPlanUri'] = self.__get_build_plan_by_name(build_plan_name)['uri']

    def __get_os_voume_by_name(self, name):
        os_volume = self.i3s_client.os_volumes.get_by_name(name)
        if not os_volume:
            raise HPOneViewResourceNotFound(I3S_OS_VOLUME_WAS_NOT_FOUND)
        return os_volume

    def __get_build_plan_by_name(self, name):
        build_plan = self.i3s_client.build_plans.get_by('name', name)
        if build_plan:
            return build_plan[0]
        else:
            raise HPOneViewResourceNotFound(I3S_BUILD_PLAN_WAS_NOT_FOUND)

    def __absent(self, resource):
        if resource:
            self.i3s_client.golden_images.delete(resource)
            return True, GOLDEN_IMAGE_DELETED, {}
        else:
            return False, GOLDEN_IMAGE_ALREADY_ABSENT, {}

    def __download(self, data, resource):
        self.i3s_client.golden_images.download(resource['uri'], data['destination_file_path'])
        return True, GOLDEN_IMAGE_DOWNLOADED, {}

    def __download_archive(self, data, resource):
        self.i3s_client.golden_images.download_archive(resource['uri'], data['destination_file_path'])
        return True, GOLDEN_IMAGE_ARCHIVE_DOWNLOADED, {}


def main():
    GoldenImageModule().run()


if __name__ == '__main__':
    main()
