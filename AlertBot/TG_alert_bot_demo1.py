# coding=u8
import datetime
import time
import telebot
import ccxt
import pandas as pd
import pandas_ta as ta

exchange = ccxt.poloniex({'enableRateLimit': True})
exchange.load_markets()

API_KEY = ''
bot = telebot.TeleBot(API_KEY)


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    print(message.chat.id)
    bot.reply_to(message, "What's up")


# bot.polling()


symbol = 'BTC/USDT'

# 上穿告警的指定价格
cross_value = 40500

# 需要指定某个chat_id
CHAT_ID = 123456

alert_dt = datetime.datetime(1970, 1, 1, 0, 0, 0)

while True:
    time.sleep(2)
    data = exchange.fetchOHLCV(symbol, '5m', limit=100)
    bid = exchange.fetch_ticker(symbol)['bid']
    print('bid: %s' % bid)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    df['crossover'] = ta.cross_value(df['close'], cross_value)
    latest_price = df.at[len(df) - 1, 'close']
    print('latest price: %s' % round(latest_price, 2))
    latest_crossover = df.at[len(df) - 1, 'crossover']
    print('latest price: %s' % latest_crossover)
    print(df[['timestamp', 'close', 'crossover']].tail())

    alert_once = False
    now = datetime.datetime.now()
    alert_duration = now - alert_dt

    if latest_crossover == 1 and not alert_once and alert_duration.seconds / 3600 > 1:
        message = f'请注意：{symbol}价格向上穿越 {cross_value}啦😉'
        bot.send_message(CHAT_ID, message)
        alert_once = True
        alert_dt = now
