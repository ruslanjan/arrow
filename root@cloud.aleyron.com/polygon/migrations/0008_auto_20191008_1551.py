# Generated by Django 2.2.5 on 2019-10-08 09:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0007_auto_20191008_1536'),
    ]

    operations = [
        migrations.RenameField(
            model_name='problem',
            old_name='is_valid',
            new_name='is_ready',
        ),
    ]
