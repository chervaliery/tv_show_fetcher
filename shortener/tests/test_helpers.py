from django.conf import settings
from django.core.cache import cache
from django.test import TestCase

from shortener.views import _cache_key_for_path, _invalidate_cache, get_prev_path, get_random_string


class CacheKeyForPathTest(TestCase):
    def test_trailing_slash_stripped(self):
        self.assertEqual(_cache_key_for_path("Local/"), "owncloud_list::Local")
        self.assertEqual(_cache_key_for_path("Local"), "owncloud_list::Local")

    def test_nested_path(self):
        self.assertEqual(_cache_key_for_path("Local/folder/sub"), "owncloud_list::Local/folder/sub")


class InvalidateCacheTest(TestCase):
    def test_invalidate_cache_removes_key(self):
        cache_key = _cache_key_for_path("Local/test")
        cache.set(cache_key, {"path": "Local/test"}, timeout=60)
        _invalidate_cache("Local/test")
        self.assertIsNone(cache.get(cache_key))


class GetPrevPathTest(TestCase):
    def test_nested_path_returns_parent(self):
        self.assertEqual(get_prev_path("Local/folder/sub"), "Local/folder")
        self.assertEqual(get_prev_path("Local/folder"), "Local")

    def test_root_path_returns_oc_path(self):
        self.assertEqual(get_prev_path("Local"), str(settings.OC_PATH))
        self.assertEqual(get_prev_path(""), str(settings.OC_PATH))


class GetRandomStringTest(TestCase):
    def test_length(self):
        s = get_random_string(10)
        self.assertEqual(len(s), 10)

    def test_charset_lowercase_and_digits(self):
        s = get_random_string(100)
        for c in s:
            self.assertIn(c, "abcdefghijklmnopqrstuvwxyz0123456789")
