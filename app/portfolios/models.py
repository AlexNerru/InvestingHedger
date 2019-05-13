from django.db import models
from users.models import Profile
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
from scipy.stats.mstats import zscore
import cvxopt as opt
from cvxopt import blas, solvers

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

    @property
    def optimize_href(self):
        return "/portfolios/" + str(self.id) + "/optimize/"

    def get_shares(self):
        initial_price = 0
        prices = {}
        for balance in self.balance_set.all():
            price = balance.security.price_set.filter(date=self.creation_date).first()
            if price is not None:
                initial_price += price.close * balance.amount
                prices[balance.security.tiker] = price.close * balance.amount
            else:
                date = self.creation_date
                while price is None:
                    date -= timedelta(days=1)
                    price = balance.security.price_set.filter(date=date).first()
                initial_price += price.close * balance.amount
                prices[balance.security.tiker] = price.close * balance.amount
        for key, value in prices.items():
            prices[key] = value/ initial_price
        shares_string = ''
        for key, value in prices.items():
            shares_string += key + " " + "{0:.2f}".format(value) + "\n"
        return shares_string

    def get_alt_shares_string(self, weights, prices):
        weights = weights.tolist()
        for column in prices.columns:
            if "change" in column:
                prices = prices.drop(columns=[column])
        result_string = ""
        for column, weight in list(zip(prices.columns, weights)):
            result_string += column + " " + "{0:.2f}".format(weight[0]) + "\n"
        return result_string

    def get_portolio_prices(self):
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

    def get_alt_prices(self, prices, weights, money):
        weights = weights.tolist()
        for column in prices.columns:
            if "change" in column:
                prices = prices.drop(columns=[column])
        data = []
        amounts = [(weights[i][0] * money) / prices.iloc[0][i] for i in range(len(weights))]
        for index, row in prices.iterrows():
            result = 0
            for i in range(len(row)):
                result += row[i] * amounts[i]
            data.append(result)
        return data

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
            prices[column + '_change'] = prices[column].pct_change().fillna(0)
            prices = prices.drop(column, axis=1)
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
        #tbill = quandl.get("FRED/TB3MS", start_date=self.creation_date, end_date=datetime.today())
        #rrf = tbill.iloc[-1, 0]
        bar = prices['change'] * 252 * 100
        ybar = bar.mean()
        sy = bar.std()
        sharpe = (ybar) / sy
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

    def get_efficient_frontier(self, changes):
        returns = changes.to_numpy().T
        returns = np.asmatrix(returns)
        n = len(returns)

        N = 100
        mus = [10 ** (5.0 * t / N - 1.0) for t in range(N)]

        # Convert to cvxopt matrices
        S = opt.matrix(np.cov(returns))
        pbar = opt.matrix(np.mean(returns, axis=1))

        # Create constraint matrices
        G = -opt.matrix(np.eye(n))  # negative n x n identity matrix
        h = opt.matrix(0.0, (n, 1))
        A = opt.matrix(1.0, (1, n))
        b = opt.matrix(1.0)

        # Calculate efficient frontier weights using quadratic programming
        portfolios = [solvers.qp(mu * S, -pbar, G, h, A, b)['x']
                      for mu in mus]
        ## CALCULATE RISKS AND RETURNS FOR FRONTIER
        returns = [blas.dot(pbar, x) for x in portfolios]
        risks = [np.sqrt(blas.dot(x, S * x)) for x in portfolios]

        ## CALCULATE THE 2ND DEGREE POLYNOMIAL OF THE FRONTIER CURVE
        m1 = np.polyfit(returns, risks, 2)
        x1 = np.sqrt(m1[2] / m1[0])
        # CALCULATE THE OPTIMAL PORTFOLIO
        wt = solvers.qp(opt.matrix(x1 * S), -pbar, G, h, A, b)['x']
        return np.asarray(wt), returns, risks

    def rand_weights(self, n):
        ''' Produces n random weights that sum to 1 '''
        k = np.random.rand(n)
        return k / sum(k)

    def random_portfolio(self, returns):
        p = np.asmatrix(np.mean(returns, axis=1))
        w = np.asmatrix(self.rand_weights(returns.shape[0]))
        C = np.asmatrix(np.cov(returns))

        mu = w * p.T
        sigma = np.sqrt(w * C * w.T)


        # This recursion reduces outliers to keep plots pretty
        if sigma > 2:
            return self.random_portfolio(returns)
        return mu, sigma

    def get_random_portfolios(self, return_vec):
        n_portfolios = 500
        means, stds = np.column_stack([
            self.random_portfolio(return_vec)
            for _ in range(n_portfolios)
        ])
        return means, stds


class Balance(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=5, max_digits=20)


class PortfolioPrice(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(decimal_places=5, max_digits=20, default=0)
