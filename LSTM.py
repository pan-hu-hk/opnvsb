import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout

from MarketData import MarketData


def transform_data(data, look_back, price_scaler=None, volume_scaler=None):
    if price_scaler is None:
        price_scaler, volume_scaler = StandardScaler(), StandardScaler()
        close = price_scaler.fit_transform(data[['close']])
        volume = volume_scaler.fit_transform(data[['volume']][:-1])
    else:
        close = price_scaler.transform(data[['close']])
        volume = volume_scaler.transform(data[['volume']][:-1])
    open_price = price_scaler.transform(data[['open']][:-1])
    high = price_scaler.transform(data[['high']][:-1])
    low = price_scaler.transform(data[['low']][:-1])
    y = close[look_back + 1:]
    x = np.hstack((open_price, high, low, close[:-1], volume))
    x = np.array([x[i - look_back:i] for i in range(look_back, x.shape[0])])
    return x, y, price_scaler, volume_scaler


def get_model(look_back):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, 5)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model


def add_lstm_prediction(train_data, test_data, look_back):
    test_data_temp = pd.concat([train_data.tail(look_back + 1), test_data])
    train_x, train_y, price_scaler, volume_scaler = transform_data(train_data, look_back)
    test_x, *_ = transform_data(test_data_temp, look_back, price_scaler, volume_scaler)
    model = get_model(look_back)
    model.fit(train_x, train_y, epochs=100, batch_size=32)
    test_data['predicted_close'] = [i[0] for i in price_scaler.inverse_transform(model.predict(test_x))]
    return test_data


market_data = MarketData('btcusd').data
monthly_data = [market_data[market_data.month == m] for m in market_data.month.unique()]
predicted_data = []
for train, test in zip(monthly_data[:-1], monthly_data[1:]):
    predicted_data.append(add_lstm_prediction(train.copy(), test.copy(), look_back=10))
pd.concat(predicted_data).to_csv('data/btcusd.lstm.csv', index=False)
