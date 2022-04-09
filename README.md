## Table of Content
* [Strategies](#strategies)
  * [Volume Index](#volume-index)
  * [LSTM Price Predictor](#lstm-price-predictor)
* [Code Structure](#code-structure)
  * [Helper Classes](#helper-classes)
  * [Strategy Classes](#strategy-classes)
* [Back-testing Result](#back-testing-result)
  * [Data Used](#data-used)
  * [Approach](#approach)
  * [Volume Index Result](#volume-index-result)
  * [LSTM Price Predictor Result](#lstm-price-predictor-result)

## Strategies
- To simplify the problem, the assumption is that only long position is allowed

### Volume Index
- This strategy utilizes two technical indicators ([definition](https://en.wikipedia.org/wiki/Negative_volume_index) on Wikipedia)
  * Positive Volume Index (PVI)
  * Negative Volume Index (NVI)
- The reason of choosing these indicators is that these are the most useful technical indicator factors when I built the price prediction model at work
- The calculation of NVI and PVI is shown in below code
  ```python
  data['prevVolume'] = data.volume.shift(1)
  data['prevClose'] = data.close.shift(1)
  data['nvi'] = data.apply(lambda x: x['close'] / x['prevClose'] if x['volume'] < x['prevVolume'] else 1, axis=1)
  data.nvi = data.nvi.cumprod()
  data['pvi'] = data.apply(lambda x: x['close'] / x['prevClose'] if x['volume'] > x['prevVolume'] else 1, axis=1)
  data.pvi = data.pvi.cumprod()
  ```
- The hypothesis is that NVI above long term average indicates a bull market and PVI below the long term average indicates a bear market.
- For this strategy, the signals are generated in below conditions
  * If both NVI and PVI are above the long term average, buy order will be placed
  * If both NVI and PVI are below the long term average, sell order will be placed

### LSTM Price Predictor
- This strategy utilizes the predicted bin close price produced by LSTM model 
- The model features are the past 10 OHLC prices and volume data
- The model is re-trained every month using previous month's data to predict the coming month's price
- The reason of choosing this model is to have a try at implementing LSTM price prediction which I haven't got a chance yet
- For this strategy, the signals are generated in below conditions
  * If the predicted close price is above the open price by certain percentage, buy order will be placed
  * If the predicted close price is below the open price by certain percentage, buy order will be placed

## Code Structure
- `run.py` is the entry point of all the logic paths
### Helper Classes
#### MarketData
- Read the data from csv file and do some further processing
- Custom `__iter__` function using `yield` to go through the data line by line 
#### Performance
- Join the market data, and the trade history of a strategy to calculate PnL history
- Generate performance report and plots
#### LSTM
- Train LSTM model at monthly basis and predict the close price for the next month
- Save the predicted price to file for back-testing

### Strategy Classes
#### Base Strategy: defines the structure of a strategy
- `calculate` is used to calculate indicators used by strategy on the fly, like NVI or PVI
- `reset` resets the strategy parameters, used when parameters are optimized
- `order` determines the trade details if buy or sell order is placed
    - Fee and slippage are set as 5 bps
    - Close price is used as the trade price
    - Trade quantity is rounded to the 4th decimal point
- `handle_data` return the action (BUY = 1, SELL = -1 or nothing = 0), to be overridden per strategy
- `stop_loss` decides whether to sell the position to avoid loss or take profit
- `run` kicks off the back-testing, basically loop through each line of market data
#### Dummy Strategy: a simple buy and hold strategy to test general logic
#### VIStrategy & LSTMStrategy: implementation of the two strategies mentioned
#### Optimizer: special strategy class used to optimize strategy parameters
- The strategy has multiple runs of the same input strategy using different parameters
- The `run` function periodically reviews (monthly or every certain days) the performance of different parameters in the previous period
- Then it chooses the best one as the parameters to be used for the next period

## Back-testing
- All the results are saved in the result folder

### Data Used
- BTCUSD is used for back-testing as it is one of the most liquid names
- By examining the data, it is clear that the data before 2017 March is not that continuous
  ![Monthly Count](https://raw.github.com/pan-hu-hk/opnvsb/master/image/monthly.count.png)
- Therefore, the data used for back-testing starts from March 1st, 2017
- Starting cash balance is set as 100,000 USD

### Approach
- Narrow down the range of parameter with meaningful returns
- Run through the values within the range
- Run the optimizer using the values within the range 
- Run the optimizer using the best ones to achieve better result

### Volume Index Result
- The parameter is the window of which the long term average is calculated 
- Using short period like hours results in trading too frequent and not making a profit
- Result shows time window at day scale leads to a profitable strategy
- The range used is 1 to 10 days and all are profitable with average 6x return
- The best one is 8 days (11520 minutes), showing 25x return
- The optimizer shows 6x return using all the values and almost 10x return when excluding some less profitable values

### LSTM Price Predictor Result
- The parameter is the threshold of percentage between predicted close price and open price that triggers a signal
- Result shows half of the values are actually not profitable
- The ones that are profitable show mediocre returns, and the best is 3.5% with a return of 4x
- Upon checking of the data, it is clearly that the model doesn't do a good job for volatile cryptocurrencies
- Below is the plot of close and predicted close price in February 2020 and March 2020
- It is clear that during second half of March, the prediction is basically capped
  ![2020 Feb-Mar](https://raw.github.com/pan-hu-hk/opnvsb/master/image/lstm.2022.Feb.Mar.png)
- The issue is that the model can only predict what it has seen before
- If the price goes beyond the previous range, it cannot do anything about it
- One way to fix this is to predict the close to open change instead of the actual price
