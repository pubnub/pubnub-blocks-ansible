sys.path.insert(0, '{0}/../module/mock'.format(os.environ['PWD']))
from mock_module import VCRModule

# List of fields for which values should be hidden.
secret_headers_fields = ['X-Session-Token']
secret_post_body_fields = ['email', 'password']
secret_response_body_fields = ['token', 'email', 'first', 'last', 'phone', 'twitter',
                               'xsite_google*', 'publish_key', 'subscribe_key',
                               'secret_key']
vcr_module = VCRModule(log_file_path=os.environ.get('TEST_LOG_FILE_PATH'),
                       fixtures_dir=os.environ.get('TEST_FIXTURES_DIR'),
                       fixture_name=os.environ.get('TEST_FIXTURE_NAME'),
                       create_fixture=os.environ.get('TEST_ENABLED') == 'True',
                       secret_headers_fields=secret_headers_fields,
                       secret_post_body_fields=secret_post_body_fields,
                       secret_response_body_fields=secret_response_body_fields)
vcr_module.inject(cls=PubNubAPIClient, function_name='request')
