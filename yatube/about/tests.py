from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticPagesURLTests(TestCase):
    def setUp(self):

        self.guest_client = Client()

    def test_about_url(self):
        """Проверка доступности адреса /about/author."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_url(self):
        """Проверка доступности адреса /about/tech."""
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/about/tech/': 'about/tech.html',
            '/about/author/': 'about/author.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
