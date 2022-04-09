from copy import deepcopy
from collections import namedtuple

from MarketData import BUY, SELL
from Performance import Performance
from strategy.Base import BaseStrategy
OptimizedParams = namedtuple('OptimizedParams', 'time params train_pnl test_pnl')


class OptimizerStrategy(BaseStrategy):
    def __init__(self, strategy, market_data, ticker, capital, params_candidates, no_days=None):
        super().__init__('Optimizer', market_data, ticker, capital)
        self.strategies = [strategy(deepcopy(market_data), ticker, capital, params) for params in params_candidates]
        self.strategy = self.strategies[0]
        self.last_optimized = self.market_data.data.time.min()
        self.no_days = no_days
        self.update_monthly = no_days is None
        self.params_history = [OptimizedParams(self.last_optimized, self.strategy.params, 0, 0)]

    def update_test_pnl(self, test_pnl):
        self.params_history[-1] = self.params_history[-1]._replace(test_pnl=test_pnl)

    def run(self, start_time=None, end_time=None):
        for records in zip(*[s.market_data for s in self.strategies]):
            for strategy, record in zip(self.strategies, records):
                action = strategy.handle_data(record)
                if (strategy.position == 0 and action == BUY) or (strategy.position > 0 and action == SELL):
                    strategy.order(action, record)
            if self.update_monthly:
                to_rerun = records[0].time.month != self.last_optimized.month
            else:
                to_rerun = (records[0].time - self.last_optimized).days > self.no_days
            if to_rerun:
                # record trades, capital and position
                self.trades += [t for t in self.strategy.trades if t.time > self.last_optimized]
                capital, position = self.strategy.capital, self.strategy.position
                # find optimal strategy
                pnl = [Performance(strategy, self.capital, self.position,
                                   self.last_optimized, records[0].time).get_final_pnl()
                       for strategy in self.strategies]
                self.update_test_pnl(pnl[self.strategies.index(self.strategy)])
                self.strategy = self.strategies[pnl.index(max(pnl))]
                self.last_optimized = records[0].time
                self.params_history.append(OptimizedParams(self.last_optimized, self.strategy.params, max(pnl), 0))
                # reset all strategies
                self.capital = capital
                self.position = position
                for strategy in self.strategies:
                    strategy.reset(capital, position, [self.trades[-1]] if position > 0 else [])
        # record trades for the final leg
        self.trades += [t for t in self.strategy.trades if t.time > self.last_optimized]
        self.update_test_pnl(Performance(self.strategy, self.capital, self.position, self.last_optimized,
                                         self.market_data.data.time.values[-1]).get_final_pnl())
