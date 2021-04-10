from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.templates_url_names = {'about/author.html': 'about:author',
                                   'about/tech.html': 'about:tech'}

    def test_about_url_guest_user(self):
        """Проверка доступности страниц неавторизованному пользователю."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse(reverse_name))
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """Проверка шаблонов для адресов страниц about."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse(reverse_name))
                self.assertTemplateUsed(response, template)
