"""
Test settings: SQLite in-memory DB and dummy API values so no real calls are made.
Usage: python manage.py test --settings=tv_show_fetcher.settings_test
"""
from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Dummy values so no real API calls slip through
USER_ID = 'test_user'
USER_URL = 'https://test-api.example.com/user'
SHOW_URL = 'https://test-api.example.com/show'
MAILJET_API_KEY = 'test_key'
MAILJET_API_SECRET = 'test_secret'
YGG_PATH = 'https://test-ygg.example.com'
YGG_PASSKEY = 'test_passkey'
OC_SERVER = 'https://test-oc.example.com'
OC_USER = 'test_oc_user'
OC_PASSWORD = 'test_oc_pass'
OC_PATH = 'Local'
YOURLS_ENDPOINT = 'https://test-yourls.example.com'
YOURLS_SIGNATURE = 'test_sig'

# Avoid writing to real paths during tests
import tempfile
TEMP_DIR = tempfile.mkdtemp()
TO_ADD = tempfile.mkdtemp()
