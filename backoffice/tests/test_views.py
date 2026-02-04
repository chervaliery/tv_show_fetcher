from django.test import RequestFactory, TestCase

from backoffice.views import home_view


class HomeViewTest(TestCase):
    def test_home_returns_bonjour_monde(self):
        factory = RequestFactory()
        request = factory.get("/")
        response = home_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Bonjour monde!")
