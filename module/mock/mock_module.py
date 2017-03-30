#!/usr/bin/python
# coding: utf-8
from vcr.stubs import VCRHTTPSConnection
from ansible.module_utils.six import PY3
from ansible.module_utils._text import to_bytes, to_text
import ansible.module_utils.urls
import logging
import json
import vcr
import os

class VCRModule(object):
    """Module allow to add mocking to any classes which perform network requests.

    After VCR module initialization 'inject' method can be used to decorate specified
    class method to send all requests through mocking library.
    """

    def __init__(self, log_file_path, fixtures_dir, fixture_name, fixture_store_format='yaml',
                 create_fixture=True, redundant_headers_fields=None, secret_headers_fields=None,
                 secret_post_body_fields=None, secret_response_body_fields=None):
        """Construct account model using service response.

        :type log_file_path:                str
        :param log_file_path:               Reference on logger's file location.
        :type fixtures_dir:                 str
        :param fixtures_dir:                Reference location of directory which contain fixtures.
        :type fixture_name:                 str
        :param fixture_name:                Reference on name of fixture which should be used during
                                            requests mocking.
        :type fixture_store_format:         str
        :param fixture_store_format:        One of available fixture storing format: yaml, json
        :type create_fixture:               bool
        :param create_fixture:              Whether requests should be mocked and fixture files
                                            generated.
        :type redundant_headers_fields:     list
        :param redundant_headers_fields:    Reference on list of headers which is not required
                                            during requests processing.
        :type secret_headers_fields:        list
        :param secret_headers_fields:       Reference on list of fields which should be hidden from
                                            header fields.
        :type secret_post_body_fields:      list
        :param secret_post_body_fields:     Reference on list of fields which should be hidden from
                                            POST'ed JSON data (if content-type is set to
                                            application/json).
        :type secret_response_body_fields:  list
        :param secret_response_body_fields: Reference on list of fields which should be hidden from
                                            response JSON body (if response type is
                                            application/json).
        :rtype:  VCRModule
        :return: Initialized VCR module.
        """
        super(VCRModule, self).__init__()

        # Configure logger to record VCR interaction.
        logging.basicConfig(filename=log_file_path, level=logging.DEBUG)

        self._fixtures_dir = fixtures_dir
        self._fixture_name = fixture_name
        self._fixture_store_format = fixture_store_format
        self._create_fixture = create_fixture
        self._redundant_headers_fields = redundant_headers_fields
        self._secret_headers_fields = secret_headers_fields
        self._secret_post_body_fields = secret_post_body_fields
        self._secret_response_body_fields = secret_response_body_fields

    def _vcr(self):
        """Create and configure VCR tool.

        :rtype:  VCR
        :return: Ready to use mocking tool.
        """
        filter_headers = None
        if self._secret_headers_fields:
            filter_headers = list()
            for header_name in self._secret_headers_fields:
                filter_headers.append((header_name, '<secret-header>'))

        filter_post_body = None
        if self._secret_post_body_fields:
            filter_post_body = list()
            for field_name in self._secret_post_body_fields:
                filter_post_body.append((field_name, '<secret-value>'))

        patch = (ansible.module_utils.urls, 'CustomHTTPSConnection', VCRHTTPSConnection)
        path_generator = self._cassette_name_generator(path=self._fixtures_dir,
                                                       name=self._fixture_name)
        before_record = VCRModule._clear_sensitive_data(secret_fields=self._secret_response_body_fields,
                                                        redundant_headers_fields=self._redundant_headers_fields)
        pn_vcr = vcr.VCR(
            custom_patches=[patch], serializer=self._fixture_store_format,
            # custom_patches=[patch], serializer='pn_fixture',
            path_transformer=vcr.VCR.ensure_suffix('.{0}'.format(self._fixture_store_format)),
            record_mode='all' if self._create_fixture else 'none', decode_compressed_response=True,
            func_path_generator=path_generator, before_record_response=before_record,
            filter_headers=filter_headers, filter_post_data_parameters=filter_post_body)
        # pn_vcr.register_serializer('pn_fixture', FixtureSerializer())

        return pn_vcr

    def inject(self, function_name):
        """Inject mocking tool into target class.

        Method will create wrapper for function which is passed by name and replace function for specified
        class with new one.
        :type cls:  class
        :param cls: Reference to class inside of which mocking wrapper should be applied.
        :type function_name:  str
        :param function_name: Name of function which should be wrapped with mocking code.
        """
        VCRModule._increase_fixture_sequence_number(counter_dir=self._fixtures_dir,
                                                    fixture_name=self._fixture_name)
        import pubnub_blocks_client.core.api as api
        setattr(api, function_name, self._vcr().use_cassette(getattr(api, function_name)))

    @staticmethod
    def _cassette_name_generator(path, name):
        """Cassette name generator function.

        Reference on generator which will help to generate proper name for cassete which should be used.
        :type path:  str
        :param path: Reference location of directory which contain target cassette.
        :type name:  str
        :param name: Reference on name of cassette which should be used during requests mocking.
        :rtype:  func
        :return: Reference on name generation function.
        """
        def wrapped(_):
            """Generate path to cassette file.

            Method allow to read environment variables to set proper path to cassete file which should be
            used for mocking.
            :rtype:  str
            :return: Reference on string which represent path at which cassete file will be / is stored.
            """
            injections_count = VCRModule._fixture_sequence_number(counter_dir=path, fixture_name=name)

            return '/'.join([path, '{0}-{1}'.format(name, injections_count)])

        return wrapped

    @staticmethod
    def _fixture_sequence_number(counter_dir, fixture_name):
        """Retrieve current mocking tool injection count.

        Count how many times for same fixture mock tool has been injected into mocked module.
        :type counter_dir:   str
        :param counter_dir:  Full path to directory, where counter file should be stored.
        :type fixture_name:  str
        :param fixture_name: Name of fixture which hold data for mocking.
        :rtype:  int
        :return: Number of mocking module injections.
        """
        sequence_number = 0
        path = '/'.join([os.path.abspath(counter_dir), '{0}.counter'.format(fixture_name)])
        if os.path.exists(path):
            with open(path, mode='r') as counter:
                lines = counter.readlines()
                if lines:
                    sequence_number = int(lines[0].strip('\n'))
        return sequence_number

    @staticmethod
    def _increase_fixture_sequence_number(counter_dir, fixture_name):
        """Increment sequence number.

        Increment number of injections for particular fixture.
        :type counter_dir:   str
        :param counter_dir:  Full path to directory, where counter file should be stored.
        :type fixture_name:  str
        :param fixture_name: Name of fixture which hold data for mocking.
        """
        path = '/'.join([os.path.abspath(counter_dir), '{0}.counter'.format(fixture_name)])
        sequence_number = VCRModule._fixture_sequence_number(fixture_name=fixture_name,
                                                             counter_dir=counter_dir)
        with open(path, mode='w') as counter:
            counter.writelines([str(sequence_number + 1)])

    @staticmethod
    def _clear_sensitive_data(secret_fields, redundant_headers_fields):
        """Hide values for fields from passed list.

        It is better not to show values which has been received from PubNub service.
        :type secret_fields:             list
        :param secret_fields:            Reference on list of fields for which values should be
                                         hidden.
        :type redundant_headers_fields:  list
        :param redundant_headers_fields: Reference on list of headers which is not required during
                                         requests processing.
        :return: Reference on method which should be called by mock library.
        """
        def before_record_response(response):
            """Response pre-processing.

            Method allow to alter required parts of response body as required.
            :type response:  dict
            :param response: Reference on dictionary which represent response from service.
            :rtype:  dict
            :return: Modified response object.
            """
            headers = list(response['headers'].keys())
            """:type : list"""
            for header in (redundant_headers_fields or list()):
                if header in headers:
                    del response['headers'][header]
            json_response = json.loads(to_text(response['body']['string']))
            VCRModule._replace_values_for_keys(obj=json_response, keys=secret_fields,
                                               new_value='<secret-value>')
            string_body = json.dumps(json_response, separators=(',', ':'))
            if not PY3:
                response['body']['string'] = string_body
            else:
                response['body']['string'] = to_bytes(string_body)

            return response

        return before_record_response

    @staticmethod
    def _is_key_in_list(key, keys):
        """Check whether specified key is in list.

        Check allow  to verify against regular key as well as against keys with wildcard.
        :type key:   str
        :param key:  Reference on key against which check should be done.
        :type keys:  list
        :param keys: Reference on list of keys which should be used for reference.
        :rtype:  bool
        :return: 'True' in case if specified 'key' is inside of 'keys' list.
        """
        in_list = key in keys
        if not in_list:
            for _key in keys:
                in_list = _key.endswith('*') and key.startswith(_key[:-1])
                if in_list:
                    break

        return in_list

    @staticmethod
    def _replace_values_for_keys(obj, keys, new_value):
        """Replace values for specified keys.

        Recursive iteration through all objects and for dictionaries if key is in list of keys
        replace it's original value with 'value'.
        :param obj:       Reference on object trhough which iteration should be performed.
        :type keys:       list
        :param keys:      Reference on list of keys which should be used for reference.
        :type new_value:  str
        :param new_value: Reference on string value which should be placed instead of original value.
        """
        if isinstance(obj, dict):
            for key in obj:
                value = obj[key]
                if VCRModule._is_key_in_list(key=key, keys=keys):
                    obj[key] = new_value
                elif isinstance(value, dict) or isinstance(value, tuple) or isinstance(value, list):
                    VCRModule._replace_values_for_keys(obj=value, keys=keys, new_value=new_value)
        elif isinstance(obj, tuple) or isinstance(obj, list):
            for _, item in enumerate(obj):
                if isinstance(item, dict) or isinstance(item, tuple) or isinstance(item, list):
                    VCRModule._replace_values_for_keys(obj=item, keys=keys, new_value=new_value)
