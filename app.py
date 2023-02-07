import telebot
from telebot import types
from credentials import bot_token
import signal
import sys
import threading
from datetime import datetime, timedelta
from time import sleep
import shutil

DATABASE_FILENAME = 'database.txt'
HELP_MESSAGE = '''ВАМ НИКТО НЕ ПОМОЖЕТ'''
bot = telebot.TeleBot(bot_token, parse_mode=None)

@bot.message_handler(commands=['help'])
def send_help(message):
	bot.send_message(message.chat.id, HELP_MESSAGE)

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, "Здравствуйте, мои маленькие любители экстремизма!")

@bot.message_handler(commands=['grind'])
def grind(message):
    if message.from_user.id not in database:
        database[message.from_user.id] = 0
        print(f'user {message.from_user.username} added to database')
        bot.send_message(message.chat.id, "Вы записаны на гринд!")
    else:
        bot.send_message(message.chat.id, "Вы уже записаны на гринд. Используйте /lose, чтобы отписаться от гринда и стать неудачником")

@bot.message_handler(commands=['progress'])
def check_progress(message):
    if message.from_user.id in database:
        bot.send_message(message.chat.id, f"{message.from_user.username}: гриндишь на протяжении {database[message.from_user.id]} дней!")
    else:
        bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")

@bot.message_handler(commands=['lose'])
def lose(message):
    if message.from_user.id in database:
        del database[message.from_user.id]
        print(f'user {message.from_user.username} removed from database')
        bot.send_message(message.chat.id, "Вы ушли с пути сигма гриндсета! Чтобы не быть ничтожеством, запишитесь на грайнд с помощью /grind")
    else:
        bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    print(f'user {message.from_user.username}: {message.text}')
    bot.reply_to(message, message.text[::-1])

def save_database_to_file(sig, frame):
    print('Saving the database to file')

    # backup
    try:
        shutil.copyfile(DATABASE_FILENAME, DATABASE_FILENAME + '.bak')
    except FileNotFoundError:
        pass

    with open(DATABASE_FILENAME, 'w') as f:
        for key, value in database.items():
            print(key, value, file=f)
    print('Successfully saved the database')
    sys.exit(0)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == 'yes':
            bot.edit_message_text('Так держать!', call.message.chat.id, call.message.id)
            database[call.from_user.id] += 1
        elif call.data == 'no':
            ans = 'ну ты и пидор говно ебаное блять ничтожество сука а ну быстро возвращайся к гринду ебаная сука уу блять пидарас говна'
            bot.edit_message_text(ans, call.message.chat.id, call.message.id)
        else:
            print(f'unknown callback: {call.data}')

def grindcheck():
    print('sending the grindchecks')
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton('Да', callback_data='yes')
    item2 = types.InlineKeyboardButton('Нет', callback_data='no')
    markup.add(item1, item2)
    for entry in database:
        bot.send_message(entry, 'Гриндил ли ты сегодня?', reply_markup=markup)

def main():
    global database
    database = {}
    
    # read the database
    print('Loading the database...')
    try:
        with open(DATABASE_FILENAME) as f:
            for line in f:
                key, value = line.split()
                database[int(key)] = int(value)
        print('Database loaded successfully')
        print(database)
    except FileNotFoundError:
        pass

    signal.signal(signal.SIGINT, save_database_to_file)
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while True:
        # проверка гринда каждый день
        HOUR, MIN = 16, 30
        now = datetime.now()
        to = now.replace(hour=HOUR, minute=MIN)
        if now >= to:
            to += timedelta(days=1)
        seconds_to_wait = (to - now).total_seconds()
        print(f'waiting for {seconds_to_wait} seconds')
        sleep(seconds_to_wait)
        grindcheck()

if __name__ == '__main__':
    main()

