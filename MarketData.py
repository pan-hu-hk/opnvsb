import os
import datetime
import numpy as np
import pandas as pd
import dask.dataframe as dd

BUY = 1
SELL = -1
DATA_FOLDER = 'data'


class MarketData(object):
    def __init__(self, ticker):
        self.data = dd.read_csv(os.path.join(DATA_FOLDER, f'{ticker}.csv')).compute()
        if type(self.data.time.values[0]) is np.int64:
            self.data.time = self.data.time.map(lambda x: datetime.datetime.fromtimestamp(x / 1e3))
        else:
            self.data.time = self.data.time.map(pd.Timestamp)
        self.data['date'] = self.data.time.map(lambda x: x.date())
        self.data['month'] = self.data.date.map(lambda x: x.replace(day=1))
        self.data = self.data[self.data.month >= datetime.date(2017, 3, 1)]

    def __iter__(self):
        for row in self.data.itertuples(name='MarketDataRecord'):
            yield row


class MockMarketData(MarketData):
    def __init__(self, ticker):
        super().__init__(ticker)
        self.data = self.data.head(50000)
