#!/usr/bin/python
# coding: utf-8
from pn_test_utils import TextColor, version, run
from shutil import move
import json
import yaml
import re
import os


def normalized_fixture(fixture_content):
    fixture_content = trimmed_fixture(fixture_with_collapsed_json_values(fixture_content))
    fixture_content = fixture_with_rearranged_headers(fixture_content)
    fixture_content = fixture_with_rearranged_content(fixture_content)
    return fixture_with_normalized_vcr_format(fixture_content)


def trimmed_fixture(fixture_content):
    fixture_lines = fixture_content.split('\n')

    return '\n'.join([line[:-1] if line[-1:] == ' ' else line for line in fixture_lines])


def fixture_with_collapsed_json_values(fixture_content):
    pattern_replace = {
        # Pack HTTP headers
        '^(\\s+\"Cache-Control\":\\s\\[)\\n\\s+(.+[^\\s])\\s*?\\n\\s+(.+[^\\s])\\s*?\\n\\s+(\\],?)': '\\1 \\2 \\3 \\4',
        '^(\\s+\".+?\":\\s\\[)\\s*?\\n\\s+(\".+?\")\\s*?\\n\\s+(\\],?)': '\\1 \\2 \\3',
        # Pack response status
        '^(\\s+\"status\":\\s\\{)\\s*?\\n\\s+(.+[^\\s])\\s*?\\n\\s+(.+[^\\s])\\s*?\\n\\s+(\\})': '\\1 \\2 \\3 \\4',
        # Pack response body
        '^(\\s+\"body\":\\s\\{)\\s*?\\n\\s+(.+[^\\s])\\s*?\\n\\s+(\\},?)': '\\1 \\2 \\3'}
    for pattern in pattern_replace:
        fixture_content = re.sub(pattern, repl=pattern_replace[pattern], string=fixture_content,
                                 flags=(re.M | re.I))
        re.purge()
    return fixture_content


def fixture_with_rearranged_headers(fixture_content):
    fixture_lines = fixture_content.split('\n')
    headers_idx = [-1, -1]
    duplicate_entries = list()
    for line_idx, line in enumerate(fixture_lines):
        headers_idx[0] = line_idx + 1 if '"headers": {' in line else headers_idx[0]
        headers_idx[1] = line_idx if headers_idx[0] != -1 and '}' in line else headers_idx[1]
        if headers_idx[0] != -1 and headers_idx[1] != -1:
            headers_list = sorted(fixture_lines[headers_idx[0]:headers_idx[1]])
            for header_idx, header in enumerate(headers_list):
                if header[-1:] == ' ':
                    header = header[:-1]
                header_name_end_index = header.index(':')
                header_name = header[:header_name_end_index].title()
                header = header_name + header[header_name_end_index:]
                if header_idx != len(headers_list) - 1:
                    header += (',' if header[-1:] != ',' else '')
                elif header[-1:] == ',':
                    header = header[:-1]
                headers_list[header_idx] = header
                for stored_header_idx, stored_header in enumerate(headers_list):
                    if stored_header.lower().startswith(header_name.lower()) and stored_header_idx > header_idx:
                        duplicate_entries.append(stored_header_idx)
            headers_list = [val for idx, val in enumerate(headers_list) if idx not in duplicate_entries]

            fixture_lines[headers_idx[0]:headers_idx[1]] = headers_list
            headers_idx = [-1, -1]
            duplicate_entries = list()
    return '\n'.join(fixture_lines)


def fixture_with_rearranged_content(fixture_content):
    should_search = True
    offset = 0

    responses = re.compile('^(\\s+\"res(?:[\\d\\D]+?^\\s+\\},?){2})', flags=(re.I | re.M))
    requests = re.compile('^(\\s+\"req(?:[\\d\\D]+?^\\s+\\},?){2})', flags=(re.I | re.M))

    while should_search:
        request = requests.search(fixture_content, pos=offset)
        response = responses.search(fixture_content, pos=offset)
        if request is not None:
            request_start = min(request.start(0), response.start(0))
            request_end = max(request.end(0), response.end(0))
            request_fixture = normalized_request(fixture_content[request.start(0):request.end(0)])
            response_fixture = normalized_response(fixture_content[response.start(0):response.end(0)])
            fixture_content = fixture_content[0:request_start] + \
                ',\n'.join([request_fixture, response_fixture]) + \
                fixture_content[request_end:]
            offset = max(request.end(0), response.end(0))
        should_search = request is not None

    return fixture_content


def normalized_request(request):
    flags = (re.I | re.M)
    headers = re.findall('^(\\s+\"headers[\\d\\D]+?\\})', string=request, flags=flags)[0]
    if headers[-1:] == ',':
        headers = headers[:-1]
    method = re.findall('^(\\s+\"method.*[^\\s])', string=request, flags=flags)[0]
    if method[-1:] == ',':
        method = method[:-1]
    uri = re.findall('^(\\s+\"uri.*[^\\s])', string=request, flags=flags)[0]
    if uri[-1:] == ',':
        uri = uri[:-1]
    body = re.findall('^(\\s+\"body.*[^\\s])', string=request, flags=flags)[0]
    if body[-1:] == ',':
        body = body[:-1]
    new_request = ',\n'.join([headers, method, uri, body])
    new_request = re.sub('(^\\s+)(\"request\":\\s\\{)([\\d\\D]+?^\\s+\\},?){2}', string=request,
                         repl='\\1\\2\\n{0}\n\\1{1}'.format(new_request, '}'), flags=flags)
    if new_request[-1:] == ',':
        new_request = new_request[:-1]

    return new_request


def normalized_response(response):
    flags = (re.I | re.M)
    headers = re.findall('^(\\s+\"headers[\\d\\D]+?\\})', string=response, flags=flags)[0]
    if headers[-1:] == ',':
        headers = headers[:-1]
    status = re.findall('^(\\s+\"status.*[^\\s])', string=response, flags=flags)[0]
    if status[-1:] == ',':
        status = status[:-1]
    body = re.findall('^(\\s+\"body.*[^\\s])', string=response, flags=flags)[0]
    if body[-1:] == ',':
        body = body[:-1]
    new_response = ',\n'.join([headers, status, body])
    new_response = re.sub('(^\\s+)(\"response\":\\s\\{)([\\d\\D]+?^\\s+\\},?){2}', string=response,
                          repl='\\1\\2\\n{0}\n\\1{1}'.format(new_response, '}'), flags=flags)
    if new_response[-1:] == ',':
        new_response = new_response[:-1]

    return new_response


def fixture_with_normalized_vcr_format(fixture_content):
    return re.sub('({\\n)^(\\s+"interactions[\\d\\D]+\\])(?:,\\n)(\\s+"vers.+)(\\n})',
                  string=fixture_content, repl='\\1\\3,\\n\\2\\4', flags=(re.I | re.M))

# Restore module file from copy
module_location = 'module/pubnub_blocks.py'
module_copy_location = '.'.join([module_location, 'orig'])
if os.path.exists(module_location) and os.path.exists(module_copy_location):
    os.remove(module_location)
if os.path.exists(module_copy_location):
    move(module_copy_location, module_location)

# Temporary disabled service results mocking.
exit(0)

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

# Normalize fixtures
for file_name in fixture_dir_files:
    if file_name.endswith('.json'):
        fixture_path = '/'.join([used_fixtures_directory, file_name])
        with open(fixture_path, mode='rt') as fixture_file:
            fixture = fixture_file.read()
            updated_fixture_content = normalized_fixture(fixture)
            try:
                json.loads(updated_fixture_content)
                fixture_file.write(updated_fixture_content)
                print('Write normalized fixture: {0}'.format(file_name))
            except ValueError:
                print('Normalization failed for: {0}'.format(file_name))


# Create missing fixtures.
with open('/'.join([os.environ['PWD'], '.travis.yml']), mode='r') as travis_file:
    travis_configuration = yaml.load(travis_file.read())
    tested_versions = travis_configuration['python']
    python_versions = ['.'.join([p_version.split('.')[0], p_version.split('.')[1]])
                       for p_version in tested_versions]
source_version = version
python_versions.remove(version)
for target_python_version in python_versions:
    target_fixtures_directory = '/'.join([fixtures_directory, target_python_version])
    if not os.path.exists(target_fixtures_directory):
        run('mkdir -p "{0}"'.format(target_fixtures_directory))
        for file_name in fixture_dir_files:
            source_fixture_path = '/'.join([used_fixtures_directory, file_name])
            if file_name.endswith('.json'):
                replacements = {source_version: target_python_version,
                                source_version.replace('.', ''): target_python_version.replace('.', '')}
                target_fixture_path = '/'.join([target_fixtures_directory, file_name])
                with open(source_fixture_path, mode='r') as fixture_file:
                    fixture = fixture_file.read()
                for original_value in replacements:
                    target_value = replacements[original_value]
                    fixture = fixture.replace(original_value, target_value)
                with open(target_fixture_path, 'w') as fixture_file:
                    fixture_file.write(fixture)
