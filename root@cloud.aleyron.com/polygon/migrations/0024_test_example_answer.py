# Generated by Django 2.2.5 on 2019-10-15 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0023_auto_20191015_0241'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='example_answer',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
