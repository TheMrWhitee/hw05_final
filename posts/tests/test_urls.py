from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Тестовое название',
                                         slug='test-slug',
                                         description='Тестовое описание')
        cls.author = User.objects.create_user(username='TestUser')
        cls.no_author = User.objects.create_user(username='NoAuthorUser')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост')
        cls.templates_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group.html': reverse('posts:group_posts',
                                        kwargs={'slug': cls.group.slug}),
            'posts/new.html': reverse('posts:new_post'),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.author.username}
            ),
            'posts/post.html': reverse(
                'posts:post',
                kwargs={'username': cls.author.username,
                        'post_id': cls.post.id}
            ),
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)

    def test_url_for_guest_user(self):
        """
        Доступность URL гостевому пользователю и проверка редиректа
        недоступных страниц.
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse('posts:new_post'):
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, 302)
                else:
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, 200)
        response = self.guest_client.get(
            reverse('posts:post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
        )
        self.assertEqual(response.status_code, 302)

    def test_url_for_authorized_user(self):
        """Доступность URL авторизованному пользователю автору поста."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_url_for_no_author_user(self):
        """Доступность URL авторизованному пользователю НЕ автору поста."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse(
                        'posts:post_edit',
                        kwargs={'username': self.author.username,
                                'post_id': self.post.id},):
                    response = self.no_author_client.get(reverse_name)
                    self.assertEqual(response.status_code, 302)
                else:
                    response = self.no_author_client.get(reverse_name)
                    self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
