# Generated by Django 2.2.5 on 2019-10-31 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='is_ioi_style',
            field=models.BooleanField(default=False, max_length=256),
        ),
        migrations.AlterField(
            model_name='contest',
            name='name',
            field=models.CharField(max_length=256, unique=True),
        ),
    ]