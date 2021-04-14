import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django import forms
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from posts.models import Group, Post, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='Тестовое название',
                                         slug='test-slug',
                                         description='Тестовое описание')

        cls.post = Post.objects.create(
            text='Тестовый пост длинной более 15 символов',
            author=cls.user,
            group=cls.group
        )
        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group.html': reverse('posts:group_posts',
                                        kwargs={'slug': 'test-slug'}),
            'posts/new.html': reverse('posts:new_post')
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_in_template_index(self):
        """
        Шаблон index сформирован с правильным контекстом.
        При создании поста с указанием группы,
        этот пост появляется на главной странице сайта.
        """
        response = self.authorized_client.get('/')
        last_post = response.context['page'][0]
        self.assertEqual(last_post, self.post)

    def test_context_in_template_group(self):
        """
        Шаблон group сформирован с правильным контекстом.
        При создании поста с указанием группы,
        этот пост появляется на странице этой группы.
        """
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'})
        )
        test_group = response.context['group']
        test_post = response.context['page'][0].__str__()
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_post, self.post.__str__())

    def test_context_in_template_new_post(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))

        form_fields = {'group': forms.fields.ChoiceField,
                       'text': forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_in_post_edit_template(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}),
        )
        self.assertEqual(response.context['post'].text,
                         self.post.text)

    def test_context_in_template_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        profile = {'post_count': self.user.posts.count(),
                   'author': self.post.author}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

        test_page = response.context['page'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_context_in_template_post(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post', kwargs={'username': self.user.username,
                                          'post_id': self.post.id})
        )

        profile = {'post_count': self.user.posts.count(),
                   'author': self.post.author,
                   'post': self.post}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_post_not_add_another_group(self):
        """
        При создании поста с указанием группы,
        этот пост НЕ попал в группу, для которой не был предназначен.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page'][0]
        group = post.group
        self.assertEqual(group, self.group)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер {count}',
                author=cls.user)

    def test_first_page_containse_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page').object_list), 3)


class ErrorPagesTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_url_names = {
            'misc/404.html': reverse('posts:404'),
            'misc/500.html': reverse('posts:500'),
        }

    def test_page_not_found(self):
        """Возвращает ли сервер код 404, если страница не найдена."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, 404)


class PostImagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                         b'\x01\x00\x80\x00\x00\x00\x00\x00'
                         b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                         b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                         b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                         b'\x0A\x00\x3B')

        cls.uploaded = SimpleUploadedFile(name='small.gif',
                                          content=cls.small_gif,
                                          content_type='image/gif')

        cls.user = User.objects.create_user(username='TestUser2')

        cls.group = Group.objects.create(title='Тестовое название',
                                         slug='test-slug2',
                                         description='Тестовое описание')

        cls.post = Post.objects.create(text='Тестовый пост с картинкой',
                                       author=cls.user,
                                       group=cls.group,
                                       image=cls.uploaded)

        cls.pages_names = [reverse('posts:index'),
                           reverse('posts:profile',
                                   kwargs={'username': 'TestUser2'}),
                           reverse('posts:group_posts',
                                   kwargs={'slug': 'test-slug2'})]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_context(self):
        """
        При выводе поста с картинкой изображение передаётся в словаре context.
        """
        for reverse_name in self.pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTrue(response.context['page'][0].image)

    def test_image_in_context_post_page(self):
        """
        На странице поста изображение передаётся в словаре context.
        """
        response = self.guest_client.get(
            reverse('posts:post', kwargs={'username': self.user.username,
                                          'post_id': self.post.id})
        )
        self.assertTrue(response.context['post'].image)


class CacheTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.post = Post.objects.create(text='Первый пост', author=self.user)

    def test_index_page_cache(self):
        """Проверка 20 секундной задержи обновления страницы index."""
        response = self.guest_client.get(reverse('posts:index'))
        page = response.content
        Post.objects.create(text='Второй пост', author=self.user)
        response = self.guest_client.get(reverse('posts:index'))
        cache_page = response.content
        self.assertEqual(page, cache_page)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        page_new_cache = response.content
        self.assertNotEqual(page, page_new_cache)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.author = User.objects.create_user(username='Author')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(text='Тестовый пост',
                                       author=cls.user)

    def test_authorized_client_comment(self):
        """Только авторизованный пользователь может оставлять комментарии."""
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'username': self.user,
                                                 'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 302)
        response = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={'username': self.user,
                                                 'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_authorized_client_follow(self):
        """Только авторизованный пользователь может подписываться."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 1)

        self.guest_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 1)

    def test_authorized_client_unfollow(self):
        """Только авторизованный пользователь может удалять из подписок."""
        Follow.objects.create(user=self.user, author=self.author)
        self.guest_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 1)

        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 0)

    def test_new_post_follower(self):
        """В ленте появляется новая запись от того на кого подписан."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        Post.objects.create(text='Пост для ленты', author=self.author)
        Post.objects.create(text='Пост для главной', author=self.user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count = len(response.context['page'])
        self.assertEqual(count, 1)
        author = response.context['page'][0].author
        self.assertEqual(author, self.author)
