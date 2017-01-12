# PubNub BLOCKS module for [Ansible](https://www.ansible.com)

[![Build Status](https://travis-ci.com/pubnub/pubnub-blocks-ansible.svg?token=TdtszNJ6Stg2gW33kobQ&branch=master)](https://travis-ci.com/pubnub/pubnub-blocks-ansible)

## Description
This module provide ability to manage PubNub blocks during deployment automation process with [Ansible](https://www.ansible.com).  
Module allow to perform next actions:  
1. [Create and delete blocks](#create-and-delete-blocks)  
2. [Create and delete block's event handlers](#create-and-delete-blocks-event-handlers)  
3. [Start and stop blocks](#start-and-stop-blocks)  
4. [Change some block information](#change-some-block-information)  
5. [Change event handlers information](#change-event-handlers-information)  

Module use BLOCKS [REST API](https://www.pubnub.com/docs/blocks/restful-api) to perform all actions on user behalf.

## Installation  
At this moment module is not part of [Ansible](https://www.ansible.com) and should be installed manually:  
1. Download module from [repository](https://raw.githubusercontent.com/pubnub/pubnub-blocks-ansible/master/module/pubnub_blocks.py).  
2. Place it into Ansible modules directory (or directory for custom modules).  
  1. If you already have directory where custom modules is stored please add [pubnub_blocks.py](https://raw.githubusercontent.com/pubnub/pubnub-blocks-ansible/master/module/pubnub_blocks.py) there.  
  2. If this is first your custom module, you need to find and update `ansible.cfg` file to include `library` assignment in _[defaul]_ section like [here](https://raw.githubusercontent.com/pubnub/pubnub-blocks-ansible/master/ansible.cfg) (but make sure to pass proper path to variable).  
  3. It is also possible to place custom modules in `library` directory which is on same level with `playbook.yml` file (which is used to run automated integration process).  

After module placed into location about which [Ansible](https://www.ansible.com) is aware we can start adding PubNub BLOCKS management with playbook.

## Module usage  
This section include basic module usage examples.  
Module designed to be efficient and in case if multiple calls to module should be done with single play in playbook it is possible to use _cached_ account information. During module usage it is possible to register variable into which _cached_ data will be placed and it can be passed to next module call (as _cache_ parameter).  
For block management it is required:  
1. Active PubNub account (can be created [here](https://admin.pubnub.com/#/register))
2. Name of PubNub application (it can be found [here](https://admin.pubnub.com) after authorization)
3. Name of application's keyset (it can be found after click on desired application from [this](https://admin.pubnub.com) page)  

Module use _names_ because it is hard to get and remember application's or keyset's identifier which is assigned by PubNub service.  
Each module call contain information identical for every scenario:  

```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: '{{ block_name }}'
  description: 'Some new block'
```  
or next in case if _caching_ has been used:
```yml
pubnub_blocks:
  cache: '{{ module_cache }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: '{{ block_name }}'
```  

### Create and delete blocks  
These block states managed by passing appropriate value to `state` parameter: **present** (to create or ensure created) or **absent** (to removed or ensure removed). `state` by default set to **present** and may be ignored in block configuration.  
_Block_ name can only contain a-z, A-Z, 0-9, spaces and the - and _ characters.  
Here is an example of single block creation:  
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  description: 'This is test block'
```  
To remove block:  
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  state: absent
```  

### Create and delete block's event handlers  
These event handler states managed by passing appropriate value to `state` parameter: **present** (to create or ensure created) or **absent** (to removed or ensure removed). `state` by default set to **present** and may be ignored in event handler configuration.  
_Name_ name can only contain a-z, A-Z, 0-9, spaces and the - and _ characters.  
Event handlers listen for event using specified _channels_ name. Processing triggered by one of available _event_: `js-before-publish`, `js-after-publish`, `js-after-presence`.  
Event handler need code which will process _event_. Code should be written using **JavaScript** language and stored at path which is specified as _src_.
Here is an example of event handlers creation:  
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  event_handlers:
    -
      src: 'sources/eh1.js'
      name: 'Event Handler 1'
      channels: 'eh-channel-1'
      event: 'js-before-publish'
    -
      src: 'sources/eh2.js'
      name: 'Event Handler 2'
      channels: 'eh-channel-2'
      event: 'js-before-publish'
```  
To remove any handler **absent** should be passed for it state:  
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  event_handlers:
    -
      name: 'Event Handler 1'
      state: absent
```  

### Start and stop blocks  
These block states managed by passing appropriate value to `state` parameter: **start** (to launch or ensure started) or **stop** (to stop or ensure stopped). Only BLOCKS with event handlers can manage their operation state.  
Here is example how block can be launched after creation:  
```yml
- name: Create block with event handlers
  register: module_cache
  pubnub_blocks:
    email: '{{ email }}'
    pwd: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    block: 'Test Block 1'
    event_handlers:
      -
        src: 'sources/eh1.js'
        name: 'Event Handler 1'
        channels: 'eh-channel-1'
        event: 'js-before-publish'
      -
        src: 'sources/eh2.js'
        name: 'Event Handler 2'
        channels: 'eh-channel-2'
        event: 'js-before-publish'
- name: Start block
  pubnub_blocks:
    cache: '{{ module_cache | default({}) }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    block: 'Test Block 1'
    state: start
```  
Block can be stopped as shown below:  
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  state: stop
```

### Change some block information  
It is possible to change basic block information like: _name_ and _description_. This may be required in really rare cases (like one block should replace existing one but keep it accessible):
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  description: 'New block description'
  changes:
    name: 'Renamed block'
```  
Be careful with renaming, because if there is more module calls which should work with this block, they should use it's new name.  

### Change event handlers information  
It is possible to modify any event handler property. Here is an example how event and handler's name can be changed (using previous example as start point of BLOCKS state):  
```yml
pubnub_blocks:
  email: '{{ email }}'
  pwd: '{{ password }}'
  application: '{{ app_name }}'
  keyset: '{{ keyset_name }}'
  block: 'Test Block 1'
  event_handlers:
    -
      name: 'Event Handler 2'
      event: 'js-after-publish'
      changes:
        name: 'New Event Handler Name'
    -
```  
