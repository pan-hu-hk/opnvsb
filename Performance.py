import os
import datetime
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from MarketData import BUY, SELL
COLS = ['position', 'cash', 'value', 'close', 'total_value', 'cumulative_pnl']
NO_DAYS = 365


def group_performance(df, frequency):
    r = df[[frequency] + COLS].groupby(frequency).last().reset_index()
    r['pnl'] = (-1 + r.total_value / r.total_value.shift(-1)).fillna(0)
    return r


def get_max_drawdown(df):
    return -1 * min(0, df.pnl.min())


class Performance(object):
    def __init__(self, strategy, initial_capital, initial_position=0, start_time=None, end_time=None, optimizer=False):
        self.ticker = strategy.ticker.upper()
        self.strategy = strategy
        self.strategy_name = strategy.name
        self.data = strategy.market_data.data
        self.trades = pd.DataFrame(data=strategy.trades)
        if start_time is not None:
            self.data = self.data[self.data.time >= start_time]
        if end_time is not None:
            self.data = self.data[self.data.time < end_time]
        if self.trades.shape[0] > 0:
            self.data = pd.merge(self.data, self.trades, on='time', how='left').fillna(0)
            self.data['position'] = self.data.trade_size * self.data.trade_side
            self.data['cash'] = -1 * self.data.position * self.data.trade_price
            self.data.position = self.data.position.cumsum() + initial_position
            self.data.cash = self.data.cash.cumsum() + initial_capital
        else:
            self.data['position'] = initial_position
            self.data['cash'] = initial_capital
        self.data['value'] = self.data.position * self.data.close
        self.data['total_value'] = self.data.value + self.data.cash
        self.data['pnl'] = (-1 + self.data.total_value / self.data.total_value.shift(-1)).fillna(0)
        self.data['cumulative_pnl'] = (-1 + self.data.total_value / self.data.total_value.iloc[0])
        self.daily = group_performance(self.data, 'date')
        self.monthly = group_performance(self.data, 'month')
        stamp = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M.%S')
        self.file_name = f'{self.ticker}.{strategy.name}.'
        if not optimizer and self.strategy.params is not None:
            self.file_name += str(self.strategy.params).replace("'", '').replace(':', '.').replace(' ', '') + '.'
        self.file_name += f'{self.daily.date.min()}.{self.daily.date.max()}.at.{stamp}'
        self.optimizer = optimizer

    def get_final_pnl(self):
        return self.data.cumulative_pnl.values[-1]

    def get_max_daily_drawdown(self):
        return get_max_drawdown(self.daily)

    def get_max_monthly_drawdown(self):
        return get_max_drawdown(self.monthly)

    def get_annual_volatility(self):
        return self.daily.pnl.std() * np.sqrt(NO_DAYS)

    def get_average_annual_return(self):
        return -1 + (1 + self.daily.cumulative_pnl.values[-1]) ** (1 / (self.daily.shape[0] / NO_DAYS))

    def get_sharpe_ratio(self):
        return self.get_average_annual_return() / self.get_annual_volatility()

    def get_average_holding_period(self):
        if self.trades.shape[0] > 0:
            buys = self.data[self.data.trade_side == BUY]
            sells = self.data[self.data.trade_side == SELL]
            if buys.shape[0] > sells.shape[0]:
                buys = buys[:-1]
            if buys.shape[0] > 0:
                times = pd.DataFrame(data={'buy': buys.time.values, 'sell': sells.time.values})
                times['duration'] = times.sell - times.buy
                return times.duration.map(lambda x: x.total_seconds() / 60).mean()
        return 0

    def get_win_ratio(self):
        if self.trades.shape[0] > 0:
            buys = self.data[self.data.trade_side == BUY]
            sells = self.data[self.data.trade_side == SELL]
            if buys.shape[0] > sells.shape[0]:
                buys = buys[:-1]
            if buys.shape[0] > 0:
                prices = pd.DataFrame(data={'buy': buys.trade_price.values, 'sell': sells.trade_price.values})
                return prices[prices.sell > prices.buy].shape[0] / prices.shape[0]
        return 0

    def get_trades_per_day(self):
        if self.trades.shape[0] > 0:
            return self.data[self.data.trade_side == BUY].shape[0] / self.daily.shape[0]
        return 0

    def plot(self, save_csv=False):
        figure, axis = plt.subplots(5, 1, figsize=(15, 25))
        axis[0].text(0, 0, self.__repr__(), fontsize=18)
        axis[0].set_axis_off()
        sns.lineplot(data=self.daily, x='date', y='total_value', ax=axis[1])
        sns.lineplot(data=self.daily, x='date', y='close', ax=axis[2])
        sns.lineplot(data=self.daily, x='date', y='pnl', ax=axis[3])
        sns.lineplot(data=self.daily, x='date', y='position', ax=axis[4])
        figure.savefig(os.path.join('result', f'{self.file_name}.png'))
        if save_csv:
            self.to_csv()

    def to_csv(self):
        self.data.to_csv(os.path.join('result', f'{self.file_name}.csv'), index=False)

    def __repr__(self):
        name = 'Optimizer.' + self.strategy.strategies[0].name if self.optimizer else self.strategy_name
        r = f'''
            Performance Report
            Strategy:                   {name}  
            Ticker:                     {self.ticker}
            Start Date:                 {self.daily.date.min()}
            End Date:                   {self.daily.date.max()}
            Overall PnL:                {self.daily.cumulative_pnl.values[-1]:.2%}
            Average Annual Return:      {self.get_average_annual_return():.2%}
            Max Daily Drawdown:         {self.get_max_daily_drawdown():.2%}
            Max Monthly Drawdown:       {self.get_max_monthly_drawdown():.2%}
            Sharpe Ratio (Rf = 0):      {self.get_sharpe_ratio():.2%}
            Winning Ratio:              {self.get_win_ratio():.2%}
            Trades Per Day:             {self.get_trades_per_day():.2f}
            Average Holding Period:     {self.get_average_holding_period():.2f} minutes
        '''
        if self.optimizer:
            history = pd.DataFrame(data=self.strategy.params_history)
            history.params = history.params.map(str)
            history.to_csv(os.path.join('result', f'{self.file_name}.params.csv'), index=False)
            usage = history.groupby('params').time.count().reset_index().sort_values(by='time')
            usage.time = usage.time / history.shape[0]
            avg_pnl = history.groupby('params').test_pnl.mean().reset_index().sort_values(by='test_pnl')
            cum_pnl = history.groupby('params').test_pnl.apply(lambda x: (x + 1).prod()).reset_index()
            cum_pnl = cum_pnl.sort_values(by='test_pnl')
            cum_pnl.test_pnl = cum_pnl.test_pnl - 1
            r += f'''
            Most used param:            {usage.params.values[-1]}, usage {usage.time.values[-1]:.2%}
            Least used param:           {usage.params.values[0]}, usage {usage.time.values[0]:.2%}
            Best avg pnl param:         {avg_pnl.params.values[-1]}, pnl {avg_pnl.test_pnl.values[-1]:.2%}
            Worst avg pnl param:        {avg_pnl.params.values[0]}, pnl {avg_pnl.test_pnl.values[0]:.2%}
            Best cum param:             {cum_pnl.params.values[-1]}, pnl {cum_pnl.test_pnl.values[-1]:.2%}
            Worst cum param:            {cum_pnl.params.values[0]}, pnl {cum_pnl.test_pnl.values[0]:.2%}
            '''
        else:
            r += f'''
            Strategy param:             {self.strategy.params}
            '''
        return r
