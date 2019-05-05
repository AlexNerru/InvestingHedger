from django.db import models
from users.models import Profile
from datetime import datetime, timedelta, date
from django.core.exceptions import ValidationError
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
from scipy.stats.mstats import zscore
from django.db.models.signals import post_save
from django.dispatch import receiver

import quandl

quandl.ApiConfig.api_key = 'PZ9S3Kpy4Hvuy9t2cxqo'

class Sector(models.Model):
    name = models.CharField(unique=True, max_length=100)


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

    @classmethod
    def get_all_tikers(cls):
        return [security.tiker for security in Security.objects.all()]



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
    creation_date = models.DateField()
    securities = models.ManyToManyField(
        Security,
        through='Balance',
        through_fields=('portfolio', 'security'),
    )

    # def safe(self, *args, **kwargs):
    #    self.__create_portfolio_prices()
    #    super(Portfolio, self).save(*args, **kwargs)

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
    def not_empty(self):
        return self.balance_set.count() > 0

    @property
    def get_profit_percent(self):
        profit = self.get_profit_cu()
        initial_price = 0
        for balance in self.balance_set.all():
            price = balance.security.price_set.filter(date=self.creation_date).first()
            if price is not None:
                initial_price += price.close * balance.amount
            else:
                date = self.creation_date
                while price is None:
                    date -= timedelta(days=1)
                    price = balance.security.price_set.filter(date=date).first()
                initial_price += price.close * balance.amount
        value = (profit / initial_price) * 100
        return "{0:.2f}".format(value)

    @property
    def href(self):
        return "/portfolios/" + str(self.id)

    @property
    def delete_href(self):
        return "/portfolios/" + str(self.id) + "/delete/"

    def get_shares_buy(self, bal):
        total_price = 0
        for balance in self.balance_set.all():
            total_price += balance.amount * balance.buy_price
        return (bal.amount * bal.buy_price) / total_price

    def get_prices(self):
        security_ids = ",".join([str(balance.security_id) for balance in self.balance_set.all()])
        query = "SELECT p.date, p.close, p.security_id, b.amount " \
                "FROM portfolios_price p INNER JOIN portfolios_balance b ON portfolio_id = {} " \
                "WHERE p.security_id=b.security_id AND b.security_id IN ({}) AND p.security_id IN ({}) " \
                "AND (date > '{}') AND (date <= '{}');"
        formatted = query.format(self.id,
                                 security_ids, security_ids,
                                 self.creation_date.strftime('%Y-%m-%d'),
                                 self.get_latest_common_price_date().strftime('%Y-%m-%d'))
        engine = create_engine('sqlite:///db.sqlite3', echo=False)
        df = pd.read_sql_query(formatted, con=engine, index_col='date')
        df['price'] = df.close * df.amount
        data = df[['price']]
        data = data.groupby(by='date').sum()
        return data

    # TODO: refactor to different buy dates
    def get_prices_one_date(self):
        d = {'date': [], 'price': []}
        date_counter = self.creation_date
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
        prices['change'] = prices['price'].pct_change().fillna(0)
        return prices

    def get_stocks_returns(self, prices):
        for column in prices:
            prices[column+'_change'] = prices[column].pct_change().fillna(0)
            prices = prices.drop(column, axis=1 )
        return prices

    def get_beta(self, prices):
        query = "SELECT * FROM portfolios_price WHERE (security_id = 38) " \
                "AND (date > '{}') AND (date <= '{}');"
        formatted = query.format(self.creation_date.strftime('%Y-%m-%d'),
                                 self.get_latest_common_price_date().strftime('%Y-%m-%d'))
        engine = create_engine('sqlite:///db.sqlite3', echo=False)
        df = pd.read_sql_query(formatted, con=engine)
        x = prices['change'][1:] * 252 * 100
        y = df['close'].pct_change()[1:] * 252 * 100
        slope, intercept, r_value, p_value, std_err = stats.linregress(zscore(x), zscore(y))

        return "{0:.5f}".format(slope)

    def get_sharp(self, prices):
        tbill = quandl.get("FRED/TB3MS", start_date=self.creation_date, end_date=datetime.today())
        rrf = tbill.iloc[-1, 0]
        bar = prices['change'] * 252 * 100
        ybar = bar.mean() - rrf
        sy = bar.std()
        sharpe = (ybar - rrf) / sy
        return "{0:.5f}".format(sharpe)

    def get_stocks_data(self):
        engine = create_engine('sqlite:///db.sqlite3', echo=False)
        df = pd.DataFrame()
        for balance in self.balance_set.all():
            query = "SELECT * FROM \
            portfolios_price \
            WHERE(security_id = {}) \
            AND(date > '{}') \
            AND(date <= '{}');"
            formatted = query.format(balance.security_id, self.creation_date.strftime('%Y-%m-%d'),
                                     self.get_latest_common_price_date().strftime('%Y-%m-%d'))
            data = pd.read_sql_query(formatted, con=engine, index_col='date')
            df[balance.security.tiker] = data.close
        return df


class Balance(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=5, max_digits=20)


class PortfolioPrice(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(decimal_places=5, max_digits=20, default=0)
