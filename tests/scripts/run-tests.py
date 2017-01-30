#!/usr/bin/python
# coding: utf-8
from pn_test_utils import TextColor, TextStyle, version, run
from ansible.module_utils._text import to_bytes
import random
import time
import os
import re


def check_results(res, operations=0, changes=0, failed=0):
    """Check whether result conform to expected constrains or not.

    :type res:         str
    :param res:        String which represent tasks / play processing results.
    :type operations:  int
    :param operations: Number of expected overall tasks to be performed.
    :type changes:     int
    :param changes     Number of expected overall changes to be done.
    :type failed:      int
    :param failed      Number of expected overall failures.
    """
    check_results_match = re.search(pattern=results_search_pattern, string=res)
    if check_results_match is not None:
        values_doesnt_match = operations != int(check_results_match.group(1))
        values_doesnt_match = values_doesnt_match or changes != int(check_results_match.group(2))
        values_doesnt_match = values_doesnt_match or failed != int(check_results_match.group(3))
        if values_doesnt_match:
            if operations != int(check_results_match.group(1)):
                print('{0}Unexpected number of tasks. Expected {1} got {2}.{3}'.format(TextColor.RED, operations,
                                                                                       check_results_match.group(1),
                                                                                       TextColor.END))
            if changes != int(check_results_match.group(2)):
                print('{0}Unexpected number of changes. Expected {1} got {2}.{3}'.format(TextColor.RED, changes,
                                                                                         check_results_match.group(2),
                                                                                         TextColor.END))
            if failed != int(check_results_match.group(3)):
                print('{0}Unexpected number of failures. Expected {1} got {2}.{3}'.format(TextColor.RED, failed,
                                                                                          check_results_match.group(3),
                                                                                          TextColor.END))
            print('EXPECTED RESPONSE FORMAT: {0}'.format(res))
            exit(1)
    else:
        print('UNEXPECTED RESPONSE FORMAT: {0}'.format(res))
        exit(1)

# Prepare environment
print('Python version: {0}{1}{2}'.format(TextStyle.BOLD, version, TextStyle.END))
os.environ['PYTHON_VERSION'] = version
os.environ['TEST_ENABLED'] = 'False'
os.environ['TEST_FIXTURES_DIR'] = 'mock/fixtures/{0}'.format(version)
os.environ['TEST_LOG_FILE_PATH'] = '{0}/pnapivcr_debug.log'.format(os.environ['TEST_FIXTURES_DIR'])
os.environ['BAD_BLOCK_NAME'] = 'Ansible Block v{0}'.format(version)
os.environ['BLOCK_NAME'] = 'Ansible block v{0}'.format(version).replace('.', '')
os.environ['NEW_BLOCK_NAME'] = os.environ['BLOCK_NAME'] + '-changed'
os.environ['EVENT_HANDLER_1_NAME'] = 'Event Handler 1-{0}'.format(version).replace('.', '')
os.environ['EVENT_HANDLER_2_NAME'] = 'Event Handler 2-{0}'.format(version).replace('.', '')
os.environ['EVENT_HANDLER_1_CHANNEL_NAME'] = 'eh-channel-1-{0}'.format(random.random()).replace('.', '')
os.environ['EVENT_HANDLER_2_CHANNEL_NAME'] = 'eh-channel-1-{0}'.format(random.random()).replace('.', '')
expected_pass = 'expected to {0}{1}pass{2}'.format(TextColor.YELLOW, TextStyle.UNDERLINE, TextStyle.END)
expected_fail = 'expected to {0}{1}fail{2}'.format(TextColor.RED, TextStyle.UNDERLINE, TextStyle.END)
expected_ignore = 'expected to {0}{1}no changes{2}'.format(TextColor.GREEN, TextStyle.UNDERLINE, TextStyle.END)
if version.startswith('2.'):
    results_search_pattern = re.compile(pattern='ok=(\d+)\s+changed=(\d+).+failed=(\d+)', flags=(re.I | re.M))
else:
    results_search_pattern = re.compile(pattern=b'ok=(\d+)\s+changed=(\d+).+failed=(\d+)', flags=(re.I | re.M))
test_start_time = time.time()

# Check test playbook syntax.
print('{0}Verify test playbooks syntax...{2}'.format(TextColor.YELLOW, TextStyle.BOLD, TextColor.END))
run(to_bytes('ansible-playbook tests/test-prepare.yml -i tests/inventory --syntax-check -vvv'))
print('{0}>{1} Done.{2}'.format(TextColor.GREEN, TextStyle.BOLD, TextColor.END))

# Run block creation tests.
print('{0}Check block creation...{1}'.format(TextColor.YELLOW, TextColor.END))
print('{0}> Prepare:\n'.format(TextColor.CYAN) +
      '  1. Copy event handler scripts to remote (if required)\n' +
      '  2. Delete \'{0}\' block ({1}{2}){3}'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN,
                                                     TextColor.END))
os.environ['TEST_FIXTURE_NAME'] = 'cleanup'
run(to_bytes('ansible-playbook tests/test-prepare.yml -i tests/inventory -vvv'))
print('  {0}> {1}Done.{2}'.format(TextColor.GREEN, TextStyle.BOLD, TextColor.END))


# Scenario #1
print('{0}> Test scenario:\n'.format(TextColor.CYAN) +
      '  1. Try create block with bad chars in it ({1}{0})\n'.format(TextColor.CYAN, expected_fail) +
      '  2. Create \'{0}\' block ({1}{2}){3}'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN,
                                                     TextColor.END))
start_time = time.time()
os.environ['TEST_FIXTURE_NAME'] = 'bad-good-block-create'
results = run(to_bytes('ansible-playbook tests/test-scenario-1.yml -i tests/inventory -vvv'))
check_results(res=results[0], operations=2, changes=1, failed=0)
print('  {0}> {1}Passed in {2} seconds.{3}'.format(TextColor.GREEN, TextStyle.BOLD, (time.time() - start_time),
                                                   TextColor.END))

# Scenario #2
print('{0}> Test scenario:\n'.format(TextColor.CYAN) +
      '  1. Try create block duplicate ({1}{0})\n'.format(TextColor.CYAN, expected_ignore) +
      '  2. Rename \'{0}\' block to \'{1}\' ({2}{3})\n'.format(os.environ['BLOCK_NAME'], os.environ['NEW_BLOCK_NAME'],
                                                               expected_pass, TextColor.CYAN) +
      '  3. Try rename \'{0}\' block to \'{0}\' ({1}{2})\n'.format(os.environ['NEW_BLOCK_NAME'], expected_ignore,
                                                                   TextColor.CYAN) +
      '  4. Delete \'{0}\' block ({1}{2})\n'.format(os.environ['NEW_BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  5. Try delete \'{0}\' block ({1}{2}){3}'.format(os.environ['NEW_BLOCK_NAME'], expected_ignore, TextColor.CYAN,
                                                         TextColor.END))
start_time = time.time()
os.environ['TEST_FIXTURE_NAME'] = 'block-create-rename-delete'
results = run(to_bytes('ansible-playbook tests/test-scenario-2.yml -i tests/inventory -vvv'))
check_results(res=results[0], operations=5, changes=2, failed=0)
print('  {0}> {1}Passed in {2} seconds.{3}'.format(TextColor.GREEN, TextStyle.BOLD, (time.time() - start_time),
                                                   TextColor.END))

# Run event handlers creation tests.
print('{0}\nCheck event handlers creation...{1}'.format(TextColor.YELLOW, TextColor.END))

# Scenario #3
print('{0}> Test scenario:\n'.format(TextColor.CYAN) +
      '  1. Create \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  2. Add \'{0}\' to \'{1}\' block ({2}{3})\n'.format(os.environ['EVENT_HANDLER_1_NAME'],
                                                            os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  3. Add \'{0}\' to \'{1}\' block ({2}{3})\n'.format(os.environ['EVENT_HANDLER_2_NAME'],
                                                            os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  4. Try add both event handlers to \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_ignore,
                                                                            TextColor.CYAN) +
      '  5. Change event for \'Event Handler 1\' from \'js-before-publish\' to \'js-after-publish\' ({0}{1})\n'.format(
          expected_pass, TextColor.CYAN) +
      '  6. Try change event for \'Event Handler 1\' from \'js-before-publish\' to \'js-after-publish\' ({0}{1})\n'.format(
          expected_ignore, TextColor.CYAN) +
      '  7. Change code for \'Event Handler 2\' ({0}{1})\n'.format(expected_pass, TextColor.CYAN) +
      '  8. Try change code for \'Event Handler 2\' ({0}{1})\n'.format(expected_ignore, TextColor.CYAN) +
      '  9. Start \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  10. Try start \'{0}\' block ({1}{2})'.format(os.environ['BLOCK_NAME'], expected_ignore, TextColor.CYAN))
start_time = time.time()
os.environ['TEST_FIXTURE_NAME'] = 'add-change-handlers-start-block'
results = run(to_bytes('ansible-playbook tests/test-scenario-3.yml -i tests/inventory -vvv'))
check_results(res=results[0], operations=10, changes=6, failed=0)
print('  {0}> {1}Passed in {2} seconds.{3}'.format(TextColor.GREEN, TextStyle.BOLD, (time.time() - start_time),
                                                   TextColor.END))

# Scenario #4
print('{0}> Test scenario:\n'.format(TextColor.CYAN) +
      '  1. Remove both event handlers from \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass,
                                                                             TextColor.CYAN) +
      '  2. Try remove both event handlers from \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'],
                                                                                 expected_ignore, TextColor.CYAN) +
      '  3. Try stop \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_ignore, TextColor.CYAN) +
      '  4. Delete \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  5. Try delete \'{0}\' block ({1}{2}){3}'.format(os.environ['BLOCK_NAME'], expected_ignore, TextColor.CYAN,
                                                         TextColor.END))
start_time = time.time()
os.environ['TEST_FIXTURE_NAME'] = 'block-remove-stop'
results = run(to_bytes('ansible-playbook tests/test-scenario-4.yml -i tests/inventory -vvv'))
check_results(res=results[0], operations=5, changes=2, failed=0)
print('  {0}> {1}Passed in {2} seconds.{3}'.format(TextColor.GREEN, TextStyle.BOLD, (time.time() - start_time),
                                                   TextColor.END))

# Scenario #5
print('{0}> Test scenario:\n'.format(TextColor.CYAN) +
      '  1. Create \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  2. Add both event handlers to \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass,
                                                                        TextColor.CYAN) +
      '  3. Start \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  4. Try start \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_ignore, TextColor.CYAN) +
      '  5. Delete \'{0}\' block ({1}{2})\n'.format(os.environ['BLOCK_NAME'], expected_pass, TextColor.CYAN) +
      '  6. Try delete \'{0}\' block ({1}{2}){3}'.format(os.environ['BLOCK_NAME'], expected_ignore, TextColor.CYAN,
                                                         TextColor.END))
start_time = time.time()
os.environ['TEST_FIXTURE_NAME'] = 'block-create-add-handlers-start'
results = run(to_bytes('ansible-playbook tests/test-scenario-5.yml -i tests/inventory -vvv'))
check_results(res=results[0], operations=6, changes=4, failed=0)
print('  {0}> {1}Passed in {2} seconds.{3}'.format(TextColor.GREEN, TextStyle.BOLD, (time.time() - start_time),
                                                   TextColor.END))

print('{0}Test completed in {1} seconds.{2}'.format(TextColor.GREEN, (time.time() - test_start_time), TextColor.END))
