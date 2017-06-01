# playbooks to automate hpe onview

one time:
~~~
GIT_PATH=/srv/oneview-ansible
git clone https://github.com/HewlettPackard/oneview-ansible.git $GIT_PATH
sudo pip install hpOneView
~~~

env:
~~~
GIT_PATH=../../github/oneview-ansible/
export ANSIBLE_LIBRARY=$GIT_PATH/library
export PYTHONPATH=$PYTHONPATH:$ANSIBLE_LIBRARY
~~~
