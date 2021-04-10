from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(title='Тестовая группа')
        cls.post = Post.objects.create(
            text='Тестовый пост длинной более 15 символов',
            author=cls.user,
            group=cls.group
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {'text': 'Текст поста',
                          'group': 'Группа'}
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {'text': 'Содержание поста',
                            'group': 'Название группы'}
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_str_method(self):
        """В поле __str__  объекта post записано значение поля post.text
        длинной не более 15 символов."""
        post = PostModelTest.post
        expected_object_text = post.__str__()
        self.assertEqual(expected_object_text, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Тестовая группа')

    def test_str_method(self):
        """В поле __str__  объекта group записано значение поля group.title."""
        group = GroupModelTest.group
        expected_object_title = group.__str__()
        self.assertEqual(expected_object_title, str(group))
