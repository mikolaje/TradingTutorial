# coding=u8
import telebot
import time
from datetime import datetime, timedelta
import pandas as pd
import pandas_ta as ta
import finnhub

FINNHUB_API_KEY = ''
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)


TG_API_KEY = ""
bot = telebot.TeleBot(TG_API_KEY)


def my_hammer(df_, length):
    # 影线要大于body的多少倍
    factor = 2
    hl_range = df_['high'] - df_['low']
    body_hi = df_.apply(lambda x: max(x['close'], x['open']), axis=1)
    body_lo = df_.apply(lambda x: min(x['close'], x['open']), axis=1)
    body = body_hi - body_lo
    body_avg = ta.ema(body, length=length)
    small_body = body < body_avg

    # 上下影线占body的百分比
    shadow_percent = 10

    # 上影线
    up_shadow = df_['high'] - body_hi
    dn_shadow = body_lo - df_['low']
    has_up_shadow = up_shadow > shadow_percent / 100 * body
    has_dn_shadow = dn_shadow > shadow_percent / 100 * body

    # 下行趋势
    downtrend = df_['close'] < ta.ema(df_['close'], 50)
    bullish_hammer = downtrend & small_body & (body > 0) & (dn_shadow >= factor * body) & (has_up_shadow == False)

    return bullish_hammer


symbol = 'AAPL'
timeframe = 15
the_day = datetime.today() - timedelta(days=1)
now_ts = int(time.time())
from_timestamp = int(the_day.timestamp())

alert_dt = datetime(1970, 1, 1, 0, 0, 0)
while True:
    time.sleep(10)
    data = finnhub_client.stock_candles(symbol, timeframe, from_timestamp, now_ts)
    df = pd.DataFrame(data)
    df = df.rename(columns={'c': 'close', 'h': 'high', 'l': 'low', 'o': 'open', 'v': 'volume'})
    df['dt'] = pd.to_datetime(df['t'], unit='s')
    columns = ['close', 'high', 'low', 'open', 'status', 'timestamp', 'volume']
    df['hammer'] = my_hammer(df, 10)

    latest_hammer = df.iloc[-1, -1]
    latest_price = df.iloc[-1, 0]

    print(f'latest price: {latest_price}')
    print(df.tail())

    alert_once = False
    alert_duration = datetime.now() - alert_dt

    if latest_hammer and not alert_once and alert_duration.seconds / 3600 > 1:
        message = f'Hammer Bullish 做多信号 当前价格: %s  😉' % latest_price
        bot.send_message(350169008, message)
