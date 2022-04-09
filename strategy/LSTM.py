from MarketData import BUY, SELL
from strategy.Base import BaseStrategy


class LSTMStrategy(BaseStrategy):
    def __init__(self, market_data, ticker, capital, params):
        super().__init__('LSTM', market_data, ticker, capital, params)

    def handle_data(self, record):
        if (record.predicted_close / record.open - 1) > self.params['threshold']:
            return BUY
        if (1 - record.predicted_close / record.open) > self.params['threshold']:
            return SELL
        return 0
