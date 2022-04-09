import numpy as np

from strategy import *
from Performance import Performance
from MarketData import MarketData, MockMarketData
TICKER = 'btcusd'
CAPITAL = 100000


def run_dummy():
    market_data = MockMarketData(TICKER)
    strategy = DummyStrategy(market_data, TICKER, CAPITAL)
    strategy.run()
    performance = Performance(strategy, CAPITAL)
    performance.plot()


def run_vi():
    market_data = MarketData('btcusd')
    candidates = [{'window': i} for i in np.arange(1, 11) * 1440]
    for c in candidates:
        strategy = VIStrategy(market_data, TICKER, CAPITAL, c)
        strategy.run()
        Performance(strategy, CAPITAL).plot()
    optimizer = OptimizerStrategy(VIStrategy, market_data, TICKER, CAPITAL, candidates)
    optimizer.run()
    Performance(optimizer, CAPITAL, optimizer=True).plot()
    candidates = [c for c in candidates if c['window'] not in [1440, 4320, 7200, 10080, 14400, 8640]]
    optimizer = OptimizerStrategy(VIStrategy, market_data, TICKER, CAPITAL, candidates)
    optimizer.run()
    Performance(optimizer, CAPITAL, optimizer=True).plot()


def run_lstm():
    market_data = MarketData('btcusd.lstm')
    candidates = [{'threshold': i} for i in np.arange(1, 11) * 0.005]
    for c in candidates:
        strategy = LSTMStrategy(market_data, TICKER, CAPITAL, c)
        strategy.run()
        Performance(strategy, CAPITAL).plot()
    optimizer = OptimizerStrategy(LSTMStrategy, market_data, TICKER, CAPITAL, candidates)
    optimizer.run()
    Performance(optimizer, CAPITAL, optimizer=True).plot()


run_dummy()
run_vi()
run_lstm()
