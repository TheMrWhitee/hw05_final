# Generated by Django 2.2.6 on 2021-03-24 06:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20210324_0643'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(help_text='Название группы', max_length=200, verbose_name='Группа'),
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='posts.Group'),
        ),
    ]
