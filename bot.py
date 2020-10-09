import locale
import os
import time
from datetime import datetime
import pprint
import os.path

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import graphs_util

# ENV FILES
TELEGRAM_KEY = os.environ.get('CHART_TELEGRAM_KEY')
BASE_PATH = os.environ.get('BASE_PATH')

# log_file
charts_path = BASE_PATH + 'chart_bot/log_files/'

locale.setlocale(locale.LC_ALL, 'en_US')


# convert int to nice string: 1234567 => 1 234 567
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
    time_type, time_start, k_hours, k_days, tokens = 'd', 1, 0, 1, "ROT"
    if len(query_received) == 1:
        pass
    elif len(query_received) == 2:
        tokens = [query_received[1]]
    elif len(query_received) == 3:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
    elif len(query_received) == 4:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
        tokens = [query_received[-1]]
    else:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
        tokens = query_received[3:]
    return time_type, k_hours, k_days, tokens


def get_candlestick_pyplot(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    query_received = update.message.text.split(' ')

    time_type, k_hours, k_days, tokens = check_query(query_received)
    t_to = int(time.time())
    t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)

    for token in tokens:
        print("requesting coin " + token + " from " + str(k_days) + " days and " + str(k_hours) + " hours")
        path = charts_path + token + '.png'
        last_price = graphs_util.print_candlestick(token, t_from, t_to, path)
        message = "<code>" + token + " $" + str(last_price) + "</code>"
        context.bot.send_photo(chat_id=chat_id,
                               photo=open(path, 'rb'),
                               caption=message,
                               parse_mode="html")


def add_favorite_token(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    favorite_path = charts_path + username + '.txt'

    if not os.path.isfile(favorite_path):
        f = open(favorite_path, "x")
        f.close()

    with open(favorite_path) as f:
        msgs = f.readline()

    query_received = update.message.text.split(' ')

    if not len(query_received) == 2:
        context.bot.send_message(chat_id=chat_id, caption="Error. Can only add one symbol at a time")
    else:
        symbol_to_add = query_received[1]
        if symbol_to_add in msgs:
            context.bot.send_message(chat_id=chat_id, caption="Error. Looks like the symbol " + symbol_to_add + " is already in your favorites.")
        else:
            with open(favorite_path, "a") as fav_file:
                message_to_write = symbol_to_add + "\n"
                fav_file.write(message_to_write)
            context.bot.send_message(chat_id=chat_id, caption="Added" + symbol_to_add + " to your favorites.")


def main():
    updater = Updater(TELEGRAM_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('charts', get_candlestick_pyplot))
    dp.add_handler(CommandHandler('add_fav', add_favorite_token))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

commands = """
charts - Display some charts
add_fav - Add a favorite token
"""
