# Generated by Django 3.2.16 on 2023-08-15 20:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscribe',
            options={'ordering': ['-id'], 'verbose_name': 'подписка', 'verbose_name_plural': 'подписки'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['id'], 'verbose_name': 'пользователь', 'verbose_name_plural': 'пользователи'},
        ),
    ]
