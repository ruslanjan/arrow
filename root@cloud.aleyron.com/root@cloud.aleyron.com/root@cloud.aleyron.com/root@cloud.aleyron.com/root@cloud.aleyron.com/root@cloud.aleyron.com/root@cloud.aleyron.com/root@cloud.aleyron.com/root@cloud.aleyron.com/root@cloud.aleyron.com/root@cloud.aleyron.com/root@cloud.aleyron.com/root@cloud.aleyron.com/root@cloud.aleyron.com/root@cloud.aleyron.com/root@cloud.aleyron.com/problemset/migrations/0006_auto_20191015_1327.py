# Generated by Django 2.2.5 on 2019-10-15 07:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problemset', '0005_auto_20191015_1327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemsetuserprofile',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
