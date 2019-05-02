from yahoo_fin.stock_info import *
from portfolios.models import Security, Price
from sqlalchemy import create_engine
from datetime import datetime

class FinancialParser():

    @classmethod
    def parseSecurities(self, tiker):
        security = Security.objects.filter(tiker = tiker).first()
        if security is None:
            data = get_data(tiker)
            engine = create_engine('sqlite:///db.sqlite3', echo=False)
            data.to_sql('stocks_data', con=engine, if_exists='append')
            security = Security(tiker=tiker)
            security.save()
            for index, row in data.iterrows():
                date = datetime.strftime(index, '%Y-%m-%d')
                price = Price(date=date, low=row['low'], high=row['high'], open = row['open'], close = row[
                    'close'], security=security)
                price.save()

