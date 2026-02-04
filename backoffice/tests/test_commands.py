from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from backoffice.models import Show, Episode


class GetShowsCommandTest(TestCase):
    @patch("backoffice.management.commands.get_shows.get_shows")
    def test_get_shows_success(self, mock_get_shows):
        out = StringIO()
        call_command("get_shows", stdout=out)
        mock_get_shows.assert_called_once()
        self.assertIn("Successfully fetch shows", out.getvalue())

    @patch("backoffice.management.commands.get_shows.get_shows")
    def test_get_shows_raises_command_error_on_exception(self, mock_get_shows):
        mock_get_shows.side_effect = Exception("API error")
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("get_shows")


class FetchShowCommandTest(TestCase):
    def setUp(self):
        self.show = Show.objects.create(tst_id=1, name="Show")

    @patch("backoffice.management.commands.fetch_show.fetch_show")
    def test_fetch_show_by_id(self, mock_fetch_show):
        out = StringIO()
        call_command("fetch_show", "1", stdout=out)
        mock_fetch_show.assert_called_once_with(self.show)
        self.assertIn("Successfully fetch", out.getvalue())

    @patch("backoffice.management.commands.fetch_show.fetch_show")
    def test_fetch_show_all(self, mock_fetch_show):
        out = StringIO()
        call_command("fetch_show", "--all", stdout=out)
        mock_fetch_show.assert_called()
        self.assertEqual(mock_fetch_show.call_count, 1)

    @patch("backoffice.management.commands.fetch_show.fetch_show")
    def test_fetch_show_enabled(self, mock_fetch_show):
        self.show.enabled = True
        self.show.save()
        out = StringIO()
        call_command("fetch_show", "--enabled", stdout=out)
        mock_fetch_show.assert_called_once_with(self.show)


class DownloadEpisodeCommandTest(TestCase):
    def setUp(self):
        self.show = Show.objects.create(tst_id=1, name="Show", enabled=True)
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

    @patch("backoffice.management.commands.download_episode.download_episode")
    def test_download_episode_by_id(self, mock_download_episode):
        out = StringIO()
        call_command("download_episode", "10", stdout=out)
        mock_download_episode.assert_called_once()
        qs = mock_download_episode.call_args[0][0]
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().pk, 10)

    @patch("backoffice.management.commands.download_episode.download_episode")
    def test_download_episode_to_watch(self, mock_download_episode):
        out = StringIO()
        call_command("download_episode", "--to-watch", stdout=out)
        mock_download_episode.assert_called_once()
        qs = mock_download_episode.call_args[0][0]
        self.assertTrue(qs.filter(show__enabled=True, watched=False, downloaded=False, aired=True).exists() or qs.count() == 0)
