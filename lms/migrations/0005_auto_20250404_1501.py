# Generated by Django 3.0.5 on 2025-04-04 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0004_auto_20250404_1337'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='answer',
            name='is_correct',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='question',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='selected_option',
        ),
    ]
