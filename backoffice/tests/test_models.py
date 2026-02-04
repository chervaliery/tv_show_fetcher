import datetime

from django.test import TestCase

from backoffice.models import Show, Episode


class ShowModelTest(TestCase):
    def test_create_show(self):
        show = Show.objects.create(tst_id=1, name="Test Show")
        self.assertEqual(show.tst_id, 1)
        self.assertEqual(show.name, "Test Show")
        self.assertFalse(show.enabled)

    def test_show_str(self):
        show = Show.objects.create(tst_id=2, name="Another Show")
        self.assertEqual(str(show), "Another Show")

    def test_show_enabled_default(self):
        show = Show.objects.create(tst_id=3, name="Enabled Show", enabled=True)
        self.assertTrue(show.enabled)


class EpisodeModelTest(TestCase):
    def setUp(self):
        self.show = Show.objects.create(tst_id=10, name="Show")

    def test_create_episode(self):
        ep = Episode.objects.create(
            tst_id=101,
            show=self.show,
            name="Pilot",
            season=1,
            number=1,
            aired=True,
            watched=False,
        )
        self.assertEqual(ep.tst_id, 101)
        self.assertEqual(ep.show, self.show)
        self.assertEqual(ep.name, "Pilot")
        self.assertEqual(ep.season, 1)
        self.assertEqual(ep.number, 1)
        self.assertFalse(ep.downloaded)
        self.assertIsNone(ep.date)

    def test_episode_str(self):
        ep = Episode.objects.create(
            tst_id=102,
            show=self.show,
            name="Episode Two",
            season=1,
            number=2,
            aired=True,
            watched=False,
        )
        self.assertEqual(str(ep), "Show S01E02")

    def test_episode_with_date(self):
        d = datetime.date(2024, 1, 15)
        ep = Episode.objects.create(
            tst_id=103,
            show=self.show,
            name="Dated",
            season=2,
            number=1,
            date=d,
            aired=True,
            watched=False,
        )
        self.assertEqual(ep.date, d)

    def test_episode_blank_name(self):
        ep = Episode.objects.create(
            tst_id=104,
            show=self.show,
            name="",
            season=1,
            number=3,
            aired=False,
            watched=False,
        )
        self.assertEqual(ep.name, "")
        self.assertEqual(str(ep), "Show S01E03")
