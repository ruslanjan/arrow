# Generated by Django 2.2.5 on 2019-10-13 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0016_problem_is_interactive'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='memory_limit',
            field=models.IntegerField(default=256000),
        ),
        migrations.AddField(
            model_name='problem',
            name='time_limit',
            field=models.IntegerField(default=1),
        ),
    ]