# Generated by Django 2.2.5 on 2019-10-06 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0005_auto_20191007_0330'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='is_valid',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='problem',
            name='checker',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='solution',
            field=models.TextField(blank=True),
        ),
    ]