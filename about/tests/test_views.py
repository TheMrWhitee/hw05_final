from django.test import Client, TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.templates_url_names = {'about/author.html': 'about:author',
                                   'about/tech.html': 'about:tech'}

    def test_about_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени about:..., доступен."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse(reverse_name))
                self.assertEqual(response.status_code, 200)

    def test_about_page_uses_correct_template(self):
        """При запросе к about: ... применяется шаблон about/ ... .html."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse(reverse_name))
                self.assertTemplateUsed(response, template)
