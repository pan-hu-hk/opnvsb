from MarketData import BUY, SELL
from collections import namedtuple

Trade = namedtuple('Trade', 'time trade_side trade_size trade_price')


class BaseStrategy(object):
    def __init__(self, name, market_data, ticker, capital, params=None):
        self.name = name
        self.ticker = ticker
        self.market_data = market_data
        self.capital = capital
        self.position = 0
        self.trades = []
        self.params = params
        self.calculate()

    def calculate(self):
        pass

    def reset(self, capital, position, trades):
        self.capital = capital
        self.position = position
        self.trades = trades

    # TODO: cost model related to volume
    def order(self, side, record):
        slippage = 0.0005
        fee = 0.0005
        cost = slippage + fee
        trade_price = record.close * (1 + cost * side)
        position = self.position if side == SELL else round(self.capital / trade_price, 4)
        if position > 0:
            trade = Trade(time=record.time, trade_side=side, trade_size=position, trade_price=trade_price)
            self.trades.append(trade)
            self.position = 0 if side == SELL else position
            self.capital -= side * position * trade_price

    def handle_data(self, record):
        return 0

    def stop_loss(self, record, loss=-0.05, profit=0.1):
        if self.position > 0:
            pnl = record.close / self.trades[-1].trade_price - 1
            if pnl > profit or pnl < loss:
                return SELL
        return 0

    def run(self, start_time=None, end_time=None):
        for record in self.market_data:
            if start_time is not None and end_time is not None and start_time > record.time > end_time:
                pass
            action = self.handle_data(record)
            if (self.position == 0 and action == BUY) or (self.position > 0 and action == SELL):
                self.order(action, record)
