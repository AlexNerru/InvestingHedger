# Generated by Django 2.1 on 2019-05-04 12:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0012_portfolioprice'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='balance',
            name='buy_date',
        ),
        migrations.RemoveField(
            model_name='balance',
            name='buy_price',
        ),
    ]
