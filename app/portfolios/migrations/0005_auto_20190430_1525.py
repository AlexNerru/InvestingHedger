# Generated by Django 2.1 on 2019-04-30 12:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0004_auto_20190430_1514'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='price',
            name='avg',
        ),
        migrations.RemoveField(
            model_name='price',
            name='currency',
        ),
        migrations.RemoveField(
            model_name='price',
            name='exchange',
        ),
    ]
