#!/usr/bin/python
# coding: utf-8
from pn_test_utils import run, version
from ansible.module_utils._text import to_bytes
from shutil import move
import os


# Create tests inventory file which will refer to proper Python interpreter.
inventory_file_location = 'tests/inventory'
if not os.path.exists(to_bytes(inventory_file_location)):
    python_location = run('which python')[0].strip('\n')
    inventory_file_content = '[blocks]\nlocalhost ansible_connection=local ansible_python_interpreter={0}'
    run('echo \'{0}\' >{1}'.format(inventory_file_content, inventory_file_location).format(python_location))

# Prepare fixtures directory
fixtures_directory = 'tests/mock/fixtures/{0}'.format(version)
if not os.path.exists(fixtures_directory):
    run('mkdir -p "{0}"'.format(fixtures_directory))

# Remove old VCR logs if exists.
fixture_dir_files = os.listdir(fixtures_directory)
for file_name in fixture_dir_files:
    if file_name.endswith('.log'):
        os.remove('/'.join([fixtures_directory, file_name]))
        break

# Prepare for VCR injection.
module_injection_location = 'module/mock/mock_module_injection.py'
module_location = 'module/pubnub_blocks.py'
module_copy_location = '.'.join([module_location, 'orig'])

# Recover previous module version if required.
if not os.path.exists(to_bytes(module_copy_location)):
    move(module_location, module_copy_location)

# Inject VCR initialization code
with open(to_bytes(module_copy_location), mode='r') as blocks_module:
    module_code_lines = blocks_module.readlines()
    injection_line_idx = module_code_lines.index('def main():\n') - 1
    with open(to_bytes(module_injection_location), mode='r') as injection_code:
        module_code_lines.insert(injection_line_idx, '\n')
        injection_line_idx += 1
        injection_lines = injection_code.readlines()
        for line in injection_lines:
            module_code_lines.insert(injection_line_idx, line)
            injection_line_idx += 1
        module_code_lines.insert(injection_line_idx, '\n')
    with open(to_bytes(module_location), mode='w') as modified_blocks_module:
        modified_blocks_module.writelines(module_code_lines)
