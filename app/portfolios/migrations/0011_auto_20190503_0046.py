# Generated by Django 2.1 on 2019-05-02 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0010_remove_price_change'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='creation_date',
            field=models.DateField(),
        ),
    ]