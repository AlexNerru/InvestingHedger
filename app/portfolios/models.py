from django.db import models
from users.models import Profile
from datetime import datetime, timedelta, date
from django.core.exceptions import ValidationError
import pandas as pd
import numpy as np


class Security(models.Model):
    tiker = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=10, default='Company Inc.', null=True)

    class Meta:
        verbose_name_plural = "Securities"

    def get_latest_price(self):
        return self.price_set.filter(security=self).latest('date')

    def get_return_percent(self, date):
        buy_price = self.price_set.filter(date=date).first()
        if buy_price is not None:
            return self.get_latest_price().close / buy_price.close - 1
        else:
            while buy_price is None:
                date -= timedelta(days=1)
                buy_price = self.price_set.filter(date=date).first()
            return self.get_latest_price().close / buy_price.close - 1

    def get_return_cu(self, date):
        buy_price = self.price_set.filter(date=date).first()
        if buy_price is not None:
            return self.get_latest_price().close - buy_price.close
        else:
            while buy_price is None:
                date -= timedelta(days=1)
                buy_price = self.price_set.filter(date=date).first()
            return self.get_latest_price().close - buy_price.close

    def get_secutiry_returns(self, date_start):
        returns = []
        prices = self.price_set.filter(date > date_start).all()


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
    creation_date = models.DateField(auto_now_add=True)
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
            amount += balance.security.get_return_cu(date=self.creation_date) * balance.amount
        return amount

    @property
    def get_profit_percent(self):
        profit = self.get_profit_cu()
        initial_price = 0
        for balance in self.balance_set.all():
            initial_price += \
                balance.security.price_set.filter(date=self.creation_date).first().close \
                * balance.amount
        value = (profit / initial_price) * 100
        return "{0:.2f}".format(value)

    @property
    def href(self):
        return "/portfolios/" + str(self.id)

    def get_shares_buy(self, bal):
        total_price = 0
        for balance in self.balance_set.all():
            total_price += balance.amount * balance.buy_price
        return (bal.amount * bal.buy_price) / total_price

    # TODO: refactor to different buy dates
    def get_prices_one_date(self, date):
        d = {'date': [], 'price': []}
        date_counter = date
        df = pd.DataFrame()
        latest_date = self.get_latest_common_price_date()

        while date_counter <= latest_date:
            price = 0
            for balance in self.balance_set.all():
                close_price = balance.security.price_set.filter(date=date_counter).first()
                if close_price is not None:
                    price += close_price.close * balance.amount
            if price != 0:
                d['date'].append(date_counter)
                d['price'].append(price)
            date_counter += timedelta(days=1)
            df = pd.DataFrame(d)
        return df

    def get_latest_common_price_date(self):
        list_dates = []
        for balance in self.balance_set.all():
            list_dates.append(balance.security.get_latest_price().date)
        list_dates.sort()
        return list_dates[0]

    def get_earliest_buy(self):
        earliest = date(3000, 12, 31)
        for balance in self.balance_set.all():
            if (balance.buy_date < earliest):
                earliest = balance.buy_date
        return earliest

    def get_portfolio_returns(self, prices):
        prices['price'] = prices['price'].astype(float)
        prices['change']= prices['price'].pct_change().fillna(0)
        return prices


class Balance(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=5, max_digits=20)
    buy_date = models.DateField(auto_now_add=True)
    buy_price = models.DecimalField(decimal_places=5, max_digits=20)
