# coding=u8

"""
This is a demo for tutorial: https://youtu.be/MCNgl0342YE

"""

import ccxt
import schedule
import pandas as pd
import pandas_ta as ta
pd.set_option('display.max_rows', None)

import warnings
warnings.filterwarnings('ignore')

import numpy as np
from datetime import datetime
import time

exchange = ccxt.binance({
    "apiKey": '',
    "secret": '',
    'enableRateLimit': True})

exchange.load_markets()


entry_rsi = 30
exit_rsi = 40

symbol = 'SOL/USDT'
timeframe = '30m'
tf_mult = exchange.parse_timeframe(timeframe) * 1000


def indicators(data):
     data['rsi'] = data.ta.rsi(length=10)
     data['ema'] = data.ta.ema(length=200)
     return data


in_position = False
order_size = 20  # in USDT

open_orders = exchange.fetch_open_orders(symbol)


def check_buy_sell_signals(df):
    global in_position

    last_row_index = len(df.index) - 1
    latest_rsi = round(df['rsi'].iloc[-1], 2)
    latest_price = round(df['close'].iloc[-1], 2)
    latest_ema = round(df['ema'].iloc[-1], 2)
    latest_ts = df['timestamp'].iloc[-1]

    # 每次交易币的数量
    amount = order_size/latest_price

    long_condition =  (latest_rsi < entry_rsi) and (latest_price > latest_ema)
    print(f'Price: {latest_price}; RSI: {latest_rsi}; EMA: {latest_ema}')

    # 买入前提是要没有open的订单
    if open_orders:
        print('Warning: There is an open order, unable to entry')
    if long_condition and len(open_orders) == 0:
        if not in_position:
            in_position = True
            print('Long Entry')
            order = exchange.create_market_buy_order(symbol, round(order_size/latest_price, 5))
            amount = order['amount']
            print(order)
        else:
            print('Already in position')

    if in_position:
        closed_orders = exchange.fetchClosedOrders(symbol, limit=2)
        most_recent_closed_order = closed_orders[-1]
        diff = latest_ts - most_recent_closed_order['timestamp']
        last_buy_signal_cnt = int(diff / tf_mult)
        exit_condition = (latest_rsi > exit_rsi) and (last_buy_signal_cnt > 10)
        if exit_condition:
            print('Exit')
            order = exchange.create_market_sell_order(symbol, amount)
            print(order)


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
    df = pd.DataFrame(bars[:], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['dt'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = indicators(df).tail(30)

    check_buy_sell_signals(df)


schedule.every(10).seconds.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)


