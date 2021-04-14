from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст поста', help_text='Содержание поста')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group,
                              verbose_name='Группа',
                              help_text='Название группы',
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              blank=True,
                              null=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             verbose_name='Пост',
                             help_text='Добавьте комментарий',
                             on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField('Текст комментария',
                            help_text='Содержание комментария')
    created = models.DateTimeField('Добавлен', auto_now_add=True)


class Follow(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'author'],
                       name='unique_follow')]
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             null=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               null=True)
