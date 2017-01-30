#!/usr/bin/python
# coding: utf-8
from ansible.module_utils._text import to_bytes
from pn_test_utils import TextColor, version, run
from shutil import move
import yaml
import os

print('PWD: {0}'.format(os.environ['PWD']))

# Print out VCR operation results.
fixtures_directory = 'tests/mock/fixtures'
used_fixtures_directory = '/'.join([fixtures_directory, version])
fixture_dir_files = os.listdir(used_fixtures_directory)
for file_name in fixture_dir_files:
    full_path = '/'.join([used_fixtures_directory, file_name])
    # Remove old module calls counter file.
    if file_name.endswith('.counter'):
        os.remove(full_path)
    if file_name.endswith('.log'):
        with open(full_path, mode='r') as log:
            print('\nMock requests stats:\n{0}'.format('-' * 20))
            log_lines = log.readlines()
            for log_line in log_lines:
                log_line = log_line.strip('\n').replace('INFO:vcr.stubs:', '')
                if log_line.endswith('sending to real server'):
                    log_line = '{0}BAD {1}{2}'.format(TextColor.RED, log_line, TextColor.END)
                else:
                    log_line = '{0}OK  {1}{2}'.format(TextColor.GREEN, log_line, TextColor.END)
                print(log_line)
            print('{0}'.format('-' * 20))

# Create missing fixtures.
with open('/'.join([os.environ['PWD'], '.travis.yml']), mode='r') as travis_file:
    travis_configuration = yaml.load(travis_file.read())
    python_versions = ['.'.join([python_version.split('.')[0], python_version.split('.')[1]]) for python_version in travis_configuration['python']]
source_version = version
python_versions.remove(version)
for file_name in fixture_dir_files:
    source_fixture_path = '/'.join([used_fixtures_directory, file_name])
    if file_name.endswith('.json'):
        for target_python_version in python_versions:
            replacements = {source_version: target_python_version,
                            source_version.replace('.', ''): target_python_version.replace('.', '')}
            target_fixtures_directory = '/'.join([fixtures_directory, target_python_version])
            target_fixture_path = '/'.join([target_fixtures_directory, file_name])
            with open(source_fixture_path, mode='r') as fixture_file:
                fixture = fixture_file.read()
            for original_value in replacements:
                target_value = replacements[original_value]
                fixture = fixture.replace(original_value, target_value)
            if not os.path.exists(target_fixtures_directory):
                run('mkdir -p "{0}"'.format(target_fixtures_directory))
            with open(target_fixture_path, 'w') as fixture_file:
                fixture_file.write(fixture)


# Restore module file from copy
module_location = 'module/pubnub_blocks.py'
module_copy_location = '.'.join([module_location, 'orig'])
if os.path.exists(to_bytes(module_location)) and os.path.exists(to_bytes(module_copy_location)):
    os.remove(module_location)
if os.path.exists(to_bytes(module_copy_location)):
    move(module_copy_location, module_location)
