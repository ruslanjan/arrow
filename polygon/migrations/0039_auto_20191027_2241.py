# Generated by Django 2.2.5 on 2019-10-27 16:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0038_test_example_input'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='is_graded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='problem',
            name='is_sub_task',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='submission',
            name='points',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='test',
            name='points',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='submission',
            name='verdict',
            field=models.CharField(blank=True, choices=[('OK', 'OK'), ('WA', 'Wrong answer'), ('PE', 'Presentation error'), ('EOF', 'UNEXPECTED_EOF'), ('TLE', 'Time limit exceeded'), ('MLE', 'Memory limit exceeded'), ('RE', 'Runtime error'), ('CP', 'Compilation Error'), ('TE', 'Test error'), ('WTE', 'Test error'), ('UC', 'Unknown code'), ('PTS', 'POINTS')], default=None, max_length=64, null=True),
        ),
        migrations.CreateModel(
            name='TestGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.FloatField(default=0)),
                ('name', models.CharField(max_length=64)),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polygon.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionTestResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.FloatField(default=0)),
                ('time_used', models.FloatField(default=-1)),
                ('memory_used', models.IntegerField(default=-1)),
                ('verdict_message', models.CharField(default='', max_length=64)),
                ('verdict_description', models.TextField(default='')),
                ('verdict_debug_message', models.CharField(default='', max_length=64)),
                ('verdict_debug_description', models.TextField(default='')),
                ('verdict', models.CharField(blank=True, choices=[('OK', 'OK'), ('WA', 'Wrong answer'), ('PE', 'Presentation error'), ('EOF', 'Unexpected EOF'), ('TLE', 'Time limit exceeded'), ('MLE', 'Memory limit exceeded'), ('RE', 'Runtime error'), ('TE', 'Test error'), ('WTE', 'WTE'), ('UC', 'Unknown code'), ('PTS', 'POINTS')], default=None, max_length=64, null=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polygon.Submission')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='polygon.Test')),
            ],
        ),
        migrations.AddField(
            model_name='test',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='polygon.TestGroup'),
        ),
    ]