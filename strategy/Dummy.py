from MarketData import BUY, SELL
from strategy.Base import BaseStrategy


class DummyStrategy(BaseStrategy):
    def __init__(self, market_data, ticker, capital):
        super().__init__('Dummy', market_data, ticker, capital)

    def handle_data(self, record):
        if record.time.hour == 1 and record.time.minute == 1:
            return BUY
        if self.position > 0:
            pnl = abs(record.close / self.trades[-1].trade_price - 1)
            if pnl > 0.02:
                return SELL
        return 0
