from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from shortener.views import (
    home_view,
    list_view,
    shorten_view,
    delete_view,
    refresh_view,
    _cache_key_for_path,
    _invalidate_cache,
)


class HomeViewTest(TestCase):
    def test_home_redirects_to_list(self):
        request = RequestFactory().get("/")
        response = home_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("list"))


class ListViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("shortener.views.cache.set")
    @patch("shortener.views.YOURLSClient")
    @patch("shortener.views.owncloud.Client")
    def test_list_view_returns_context_with_path_and_files(self, mock_oc_client, mock_yourls, mock_cache_set):
        mock_oc = MagicMock()
        mock_oc_client.return_value = mock_oc
        mock_file = MagicMock()
        mock_file.path = "Local/file.txt"
        mock_file.attributes = {}
        mock_oc.list.return_value = [mock_file]
        mock_oc.get_shares.return_value = []

        mock_yourls_instance = MagicMock()
        mock_yourls_instance.list.return_value = []
        mock_yourls.return_value = mock_yourls_instance

        request = self.factory.get("/list/")
        response = list_view(request, path="Local")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Local", content)

    def test_list_view_uses_cache_when_available(self):
        cache_key = _cache_key_for_path("Local")
        cached = {"path": "Local", "prev_path": "Local", "list_of_files": []}
        cache.set(cache_key, cached, timeout=60)
        request = self.factory.get("/list/")
        response = list_view(request, path="Local")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Local", response.content.decode())
        cache.delete(cache_key)


class ShortenViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("shortener.views.YOURLSClient")
    @patch("shortener.views.owncloud.Client")
    def test_shorten_view_creates_short_link(self, mock_oc_client, mock_yourls):
        mock_oc = MagicMock()
        mock_oc_client.return_value = mock_oc
        mock_oc.get_shares.return_value = [
            MagicMock(share_info={"url": "https://oc.example.com/s/abc123"})
        ]
        mock_yourls_instance = MagicMock()
        mock_yourls_instance.shorten.return_value = MagicMock(shorturl="https://short/x")
        mock_yourls.return_value = mock_yourls_instance

        request = self.factory.post("/shorten", data={"path": "Local/file.txt", "txt": "mylink"})
        response = shorten_view(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("https://short/x", content)
        self.assertIn("https://oc.example.com/s/abc123", content)
        self.assertIn("Local/file.txt", content)


class DeleteViewTest(TestCase):
    @patch("shortener.views.YOURLSClient")
    def test_delete_view_redirects_to_list(self, mock_yourls):
        mock_yourls_instance = MagicMock()
        mock_yourls.return_value = mock_yourls_instance
        request = RequestFactory().get("/delete/abc")
        response = delete_view(request, keyword="abc")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("list"))
        mock_yourls_instance.delete.assert_called_once_with("abc")

    @patch("shortener.views.YOURLSClient")
    def test_delete_view_invalidates_cache_when_path_in_query(self, mock_yourls):
        cache_key = _cache_key_for_path("Local/folder")
        cache.set(cache_key, {"path": "Local/folder"}, timeout=60)
        mock_yourls.return_value = MagicMock()
        request = RequestFactory().get("/delete/abc", {"path": "Local/folder"})
        delete_view(request, keyword="abc")
        self.assertIsNone(cache.get(cache_key))


class RefreshViewTest(TestCase):
    def test_refresh_view_invalidates_cache_and_redirects(self):
        cache_key = _cache_key_for_path("Local")
        cache.set(cache_key, {"path": "Local"}, timeout=60)
        request = RequestFactory().get("/refresh/")
        response = refresh_view(request, path="Local")
        self.assertEqual(response.status_code, 302)
        self.assertIn("list", response.url)
        self.assertIsNone(cache.get(cache_key))
