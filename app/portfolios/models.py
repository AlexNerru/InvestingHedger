from django.db import models
from users.models import Profile
from datetime import datetime
from django.core.exceptions import ValidationError


class Security(models.Model):
    tiker = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=10, default='Company Inc.', null=True)

    class Meta:
        verbose_name_plural = "Securities"

    def get_latest_price(self):
        return self.price_set.filter(security=self).latest('date')

    def get_return_percent(self, buy_price):
        stock_return = self.get_latest_price().close/buy_price - 1
        return stock_return

    def get_return_cu(self, buy_price):
        return self.get_latest_price() - buy_price



class Price(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    date = models.DateField()
    low = models.DecimalField(decimal_places=5, max_digits=20)
    high = models.DecimalField(decimal_places=5, max_digits=20)
    close = models.DecimalField(decimal_places=5, max_digits=20, default=0)
    open = models.DecimalField(decimal_places=5, max_digits=20, default=0)


class Portfolio(models.Model):
    name = models.CharField(max_length=250)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    securities = models.ManyToManyField(
        Security,
        through='Balance',
        through_fields=('portfolio', 'security'),
    )

    class Meta:
        permissions = (
            ('crud portfolio', 'CRUD portfolio'),
        )

    def get_profit_cu(self):
        amount = 0
        for balance in self.balance_set.all():
            amount += balance.security.get_return_cu(balance.buy_price) * balance.amount
        return amount

    def get_profit_percent(self):
        profit = self.get_profit_cu()
        initial_price = 0
        for balance in self.balance_set.all():
            initial_price += balance.buy_price * balance.amount
        return profit/initial_price - 1

    @property
    def href(self):
        return "/porfolios/" + str(self.id)


class Balance(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=5, max_digits=20)
    buy_date = models.DateField(auto_now_add=True)
    buy_price = models.DecimalField(decimal_places=5, max_digits=20)
