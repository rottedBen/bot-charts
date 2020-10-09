import locale
import os
import time
from datetime import datetime

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import graphs_util

# ENV FILES
TELEGRAM_KEY = os.environ.get('CHART_TELEGRAM_KEY')
BASE_PATH = os.environ.get('BASE_PATH')

# log_file
charts_path = BASE_PATH + 'chart_bot/log_files/'

locale.setlocale(locale.LC_ALL, 'en_US')

# convert int to nice string: 1234567 => 1.234.567
def number_to_beautiful(nbr):
    return locale.format_string("%d", nbr, grouping=True).replace(",", " ")


def get_from_query(query_received):
    time_type = query_received[2]
    time_start = int(query_received[1])
    if time_start < 0:
        time_start = - time_start
    k_hours = 0
    k_days = 0
    if time_type == 'h' or time_type == 'H':
        k_hours = time_start
    if time_type == 'd' or time_type == 'D':
        k_days = time_start
    return time_type, time_start, k_hours, k_days


def strp_date(raw_date):
    return datetime.strptime(raw_date, '%m/%d/%Y,%H:%M:%S')


# util for get_chart_pyplot
def keep_dates(values_list):
    dates_str = []
    for values in values_list:
        dates_str.append(values[0])

    dates_datetime = []
    for date_str in dates_str:
        date_datetime = datetime.strptime(date_str, '%m/%d/%Y,%H:%M:%S')
        dates_datetime.append(date_datetime)
    return dates_datetime


def check_query(query_received):
    simple_query = False
    time_type, time_start, k_hours, k_days, tokens = 'd', 1, 0, 1, "NICE"
    if len(query_received) == 1:
        simple_query = True
    elif len(query_received) == 2:
        tokens = list(query_received[1])
    elif len(query_received) == 3:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
    elif len(query_received) == 4:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
        tokens = list(query_received[-1])
    else:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
        tokens = query_received[3: -1]
    return time_type, time_start, k_hours, k_days, simple_query, tokens


def get_candlestick_pyplot(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    global last_time_checked_price_candles

    query_received = update.message.text.split(' ')
    if update.message.from_user.first_name == 'Ben':
        print("hello me")
        last_time_checked_price_candles = 1

    time_type, time_start, k_hours, k_days, simple_query, tokens = check_query(query_received)

    t_to = int(time.time())
    t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)

    for token in tokens:
        path = charts_path + token
        last_price = graphs_util.print_candlestick(token, t_from, t_to, path)
        message = "<code>" + token + " $" + str(last_price) + "</code>"
        context.bot.send_photo(chat_id=chat_id,
                               photo=open(path, 'rb'),
                               caption=message,
                               parse_mode="html")

def main():
    updater = Updater(TELEGRAM_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('charts', get_candlestick_pyplot))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

commands = """
charts - Display some charts
"""
