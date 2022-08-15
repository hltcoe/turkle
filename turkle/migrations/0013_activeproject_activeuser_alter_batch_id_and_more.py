# Generated by Django 4.0.6 on 2022-08-08 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('turkle', '0012_auto_20210923_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveProject',
            fields=[
            ],
            options={
                'ordering': ['name'],
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('turkle.project',),
        ),
        migrations.CreateModel(
            name='ActiveUser',
            fields=[
            ],
            options={
                'ordering': ['first_name'],
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('cdh.user',),
        ),
        migrations.AlterField(
            model_name='batch',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='project',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='task',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='taskassignment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
