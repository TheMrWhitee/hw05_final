import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                         b'\x01\x00\x80\x00\x00\x00\x00\x00'
                         b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                         b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                         b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                         b'\x0A\x00\x3B')

        cls.uploaded = SimpleUploadedFile(name='small.gif',
                                          content=cls.small_gif,
                                          content_type='image/gif')

        cls.text_file = SimpleUploadedFile(name='text.txt',
                                           content='',
                                           content_type='text/plain')

        cls.author = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post_in_form(self):
        """Форма создаёт пост в базе."""
        post_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост из формы'}
        self.authorized_client.post(reverse('posts:new_post'), data=form_data)
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_create_post_with_image_in_form(self):
        """Форма создаёт пост с картинкой в базе."""
        post_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост из формы',
                     'image': self.uploaded}
        self.authorized_client.post(reverse('posts:new_post'), data=form_data)
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_create_post_with_not_image_file_in_form(self):
        """Нельзя загрузить другой файл вместо картинки."""
        form_data = {'text': 'Тестовый пост из формы',
                     'image': self.text_file}
        response = self.authorized_client.post(reverse('posts:new_post'),
                                               data=form_data,
                                               follow=True)
        error = 'Отправленный файл пуст.'
        self.assertFormError(response, 'form', 'image', error)

    def test_edit_post_in_form(self):
        """проверка редактирования поста."""
        form_data = {'text': 'Новый текст'}
        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
            data=form_data
        )
        response = self.authorized_client.get(
            reverse('posts:post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
        )
        self.assertEqual(response.context['post'].text, 'Новый текст')
