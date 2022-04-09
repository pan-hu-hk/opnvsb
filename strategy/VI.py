from MarketData import BUY, SELL
from strategy.Base import BaseStrategy


class VIStrategy(BaseStrategy):
    def __init__(self, market_data, ticker, capital, params):
        super().__init__('VI', market_data, ticker, capital, params)

    def calculate(self):
        data = self.market_data.data
        data['prevVolume'] = data.volume.shift(1)
        data['prevClose'] = data.close.shift(1)
        data['nvi'] = data.apply(lambda x: x['close'] / x['prevClose'] if x['volume'] < x['prevVolume'] else 1, axis=1)
        data.nvi = data.nvi.cumprod()
        data['pvi'] = data.apply(lambda x: x['close'] / x['prevClose'] if x['volume'] > x['prevVolume'] else 1, axis=1)
        data.pvi = data.pvi.cumprod()
        data['nviAverage'] = data.nvi.rolling(window=self.params['window']).mean()
        data['pviAverage'] = data.pvi.rolling(window=self.params['window']).mean()
        self.market_data.data = data

    def handle_data(self, record):
        if record.Index < self.params['window']:
            return 0
        if self.stop_loss(record) == SELL:
            return SELL
        if record.nvi > record.nviAverage and record.pvi > record.pviAverage:
            return BUY
        if record.nvi < record.nviAverage and record.pvi < record.pviAverage:
            return SELL
        return 0
