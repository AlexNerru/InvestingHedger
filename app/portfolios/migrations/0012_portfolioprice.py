# Generated by Django 2.1 on 2019-05-03 11:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0011_auto_20190503_0046'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=5, default=0, max_digits=20)),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolios.Portfolio')),
            ],
        ),
    ]
