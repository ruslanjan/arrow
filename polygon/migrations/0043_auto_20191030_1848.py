# Generated by Django 2.2.5 on 2019-10-30 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0042_auto_20191030_0021'),
    ]

    operations = [
        migrations.AddField(
            model_name='statement',
            name='interaction',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='statement',
            name='scoring',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='statement',
            name='tutorial',
            field=models.TextField(blank=True, default=''),
        ),
    ]
