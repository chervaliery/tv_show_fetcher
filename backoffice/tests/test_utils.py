import datetime
from unittest.mock import MagicMock, patch

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from backoffice.models import Show, Episode

User = get_user_model()
from backoffice.utils import (
    safe_filename,
    create_or_update_with_log,
    get_shows,
    fetch_show,
    send_mail,
    print_messages,
    download_episode,
    download_by_urls,
    lookup,
)


class SafeFilenameTest(TestCase):
    def test_plain_ascii(self):
        self.assertEqual(safe_filename("My.Show.S01E01"), "My.Show.S01E01")

    def test_accents_normalized(self):
        self.assertEqual(safe_filename("Café"), "Cafe")
        self.assertEqual(safe_filename("naïve"), "naive")

    def test_spaces_and_unsafe_chars_replaced(self):
        self.assertEqual(safe_filename("a b c"), "a_b_c")
        self.assertEqual(safe_filename("a/b\\c"), "a_b_c")
        self.assertEqual(safe_filename("a*b?c"), "a_b_c")

    def test_unicode_normalization(self):
        # NFKD strips combining characters
        self.assertEqual(safe_filename("é"), "e")


class CreateOrUpdateWithLogTest(TestCase):
    def setUp(self):
        self._user, _ = User.objects.get_or_create(pk=1, defaults={"username": "testuser"})

    def test_create_new_show(self):
        obj, created = create_or_update_with_log(
            Show,
            tst_id=1,
            defaults={"name": "New Show"},
        )
        self.assertTrue(created)
        self.assertEqual(obj.tst_id, 1)
        self.assertEqual(obj.name, "New Show")
        self.assertEqual(LogEntry.objects.filter(object_id=obj.pk).count(), 1)

    def test_update_when_changed(self):
        Show.objects.create(tst_id=2, name="Old Name")
        obj, created = create_or_update_with_log(
            Show,
            tst_id=2,
            defaults={"name": "New Name"},
        )
        self.assertFalse(created)
        obj.refresh_from_db()
        self.assertEqual(obj.name, "New Name")
        self.assertEqual(LogEntry.objects.filter(object_id=obj.pk).count(), 1)  # change only

    def test_no_update_when_unchanged(self):
        Show.objects.create(tst_id=3, name="Same")
        obj, created = create_or_update_with_log(
            Show,
            tst_id=3,
            defaults={"name": "Same"},
        )
        self.assertFalse(created)
        # Only one LogEntry (from initial create in test)
        self.assertEqual(LogEntry.objects.filter(object_id=obj.pk).count(), 0)


class GetShowsTest(TestCase):
    def setUp(self):
        get_user_model().objects.get_or_create(pk=1, defaults={"username": "testuser"})

    @patch("backoffice.utils.requests.get")
    def test_get_shows_creates_shows(self, mock_get):
        mock_get.return_value.json.return_value = {
            "shows": [
                {"id": 100, "name": "Show A (2020)"},
                {"id": 101, "name": "Show B & Co"},
            ]
        }
        get_shows()
        self.assertEqual(Show.objects.count(), 2)
        self.assertEqual(Show.objects.get(tst_id=100).name, "Show A")
        self.assertEqual(Show.objects.get(tst_id=101).name, "Show B and Co")


class FetchShowTest(TestCase):
    def setUp(self):
        get_user_model().objects.get_or_create(pk=1, defaults={"username": "testuser"})
        self.show = Show.objects.create(tst_id=50, name="Test Show")

    @patch("backoffice.utils.requests.get")
    def test_fetch_show_creates_episodes(self, mock_get):
        mock_get.return_value.json.return_value = {
            "episodes": [
                {
                    "id": 501,
                    "name": "Pilot",
                    "season_number": 1,
                    "number": 1,
                    "air_date": "2024-01-01",
                    "seen": False,
                },
                {
                    "id": 502,
                    "name": "Second",
                    "season_number": 1,
                    "number": 2,
                    "air_date": "2024-01-08",
                    "seen": True,
                },
            ]
        }
        fetch_show(self.show)
        self.assertEqual(Episode.objects.filter(show=self.show).count(), 2)
        ep1 = Episode.objects.get(tst_id=501)
        self.assertEqual(ep1.name, "Pilot")
        self.assertEqual(ep1.season, 1)
        self.assertEqual(ep1.number, 1)
        self.assertTrue(ep1.aired)
        self.assertFalse(ep1.watched)
        ep2 = Episode.objects.get(tst_id=502)
        self.assertTrue(ep2.watched)

    @patch("backoffice.utils.requests.get")
    def test_fetch_show_invalid_air_date(self, mock_get):
        mock_get.return_value.json.return_value = {
            "episodes": [
                {
                    "id": 503,
                    "name": "Bad Date",
                    "season_number": 1,
                    "number": 3,
                    "air_date": "not-a-date",
                    "seen": False,
                },
            ]
        }
        fetch_show(self.show)
        ep = Episode.objects.get(tst_id=503)
        self.assertFalse(ep.aired)
        self.assertIsNone(ep.date)


class SendMailTest(TestCase):
    @patch("backoffice.utils.Client")
    def test_send_mail_payload(self, mock_client_class):
        mock_send = MagicMock()
        mock_client_class.return_value.send.create = mock_send
        send_mail("Subject", "Body", "from@test.com", ["to@test.com", "to2@test.com"])
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        data = call_args[1]["data"]
        self.assertEqual(data["Messages"][0]["Subject"], "Subject")
        self.assertEqual(data["Messages"][0]["TextPart"], "Body")
        self.assertEqual(data["Messages"][0]["From"]["Email"], "from@test.com")
        self.assertEqual(len(data["Messages"][0]["To"]), 2)


class PrintMessagesTest(TestCase):
    def test_print_messages_info_and_error(self):
        request = MagicMock()
        resp = {"Item A": "success", "Item B": False}
        print_messages(request, resp)
        request._messages.add.assert_called()
        calls = [c for c in request._messages.add.call_args_list]
        self.assertEqual(len(calls), 2)


class DownloadEpisodeTest(TestCase):
    def setUp(self):
        get_user_model().objects.get_or_create(pk=1, defaults={"username": "testuser"})
        self.show = Show.objects.create(tst_id=1, name="Show")
        self.episode = Episode.objects.create(
            tst_id=10,
            show=self.show,
            name="Ep1",
            season=1,
            number=1,
            aired=True,
            watched=False,
            downloaded=False,
        )

    @patch("backoffice.utils.send_mail")
    @patch("backoffice.utils.lookup")
    def test_download_episode_success_updates_downloaded(self, mock_lookup, mock_send_mail):
        mock_lookup.return_value = "Some.Title"
        qs = Episode.objects.filter(pk=self.episode.pk)
        resp = download_episode(qs)
        self.assertTrue(resp[self.episode])
        self.episode.refresh_from_db()
        self.assertTrue(self.episode.downloaded)
        mock_send_mail.assert_called_once()

    @patch("backoffice.utils.send_mail")
    @patch("backoffice.utils.lookup")
    def test_download_episode_empty_list(self, mock_lookup, mock_send_mail):
        resp = download_episode(Episode.objects.none())
        self.assertEqual(resp, {})
        mock_lookup.assert_not_called()
        mock_send_mail.assert_not_called()


class DownloadByUrlsTest(TestCase):
    @patch("backoffice.utils.send_mail")
    @patch("backoffice.utils.lookup")
    def test_download_by_urls_with_torrent_id(self, mock_lookup, mock_send_mail):
        mock_lookup.return_value = "Title"
        resp = download_by_urls(["https://example.com/torrent/12345"])
        self.assertEqual(resp["Title"], True)
        mock_lookup.assert_called_once()
        self.assertEqual(mock_lookup.call_args[0][6], "12345")

    @patch("backoffice.utils.lookup")
    def test_download_by_urls_no_match_returns_early(self, mock_lookup):
        resp = download_by_urls(["https://example.com/no-digits"])
        self.assertEqual(resp, {})
        mock_lookup.assert_not_called()


class LookupTest(TestCase):
    @patch("backoffice.utils.torrent_parser.create_torrent_file")
    @patch("backoffice.utils.torrent_parser.parse_torrent_file")
    @patch("backoffice.utils.requests.get")
    @patch("backoffice.utils.secrets.choice")
    def test_lookup_with_torrent_id_success(self, mock_secrets, mock_get, mock_parse, mock_create):
        mock_secrets.return_value = "a"
        fake_pass = "a" * 32
        mock_get.side_effect = [
            MagicMock(json=MagicMock(return_value={"title": "My Show S01E01", "announce": f"http://tracker/{fake_pass}"})),
            MagicMock(iter_content=MagicMock(return_value=[b"x"])),
        ]
        mock_parse.return_value = {"announce": f"http://tracker/{fake_pass}"}
        result = lookup(
            "https://ygg.test",
            "name",
            "real_pass",
            "/tmp/to_add",
            "MULTi",
            "1080p",
            torrent_id="999",
        )
        self.assertEqual(result, "My_Show_S01E01")
        mock_create.assert_called_once()

    @patch("backoffice.utils.requests.get")
    def test_lookup_with_torrent_id_no_torrent_returns_false(self, mock_get):
        mock_get.return_value.json.return_value = None
        result = lookup(
            "https://ygg.test",
            "name",
            "pass",
            "/tmp",
            "MULTi",
            "1080p",
            torrent_id="999",
        )
        self.assertFalse(result)
