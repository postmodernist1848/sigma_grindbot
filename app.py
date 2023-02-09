import telebot
from telebot import types
from credentials import bot_token
import signal
import sys
import os
import threading
from datetime import datetime, timedelta
from time import sleep
import shutil
from swearing import generate_swearline

import linecache
import random

DATABASE_DIR = 'database.d'
HELP_MESSAGE = '''Этот бот позволяет вам встать на путь sigma male grindset и гриндить каждый день.

Команды:
/grind    - записаться на ежедневный грайнд
/progress - проверить собственный прогресс
/lose - уйти с пути сигмы и стать неудачником
/swear <число> - сгенерировать случайное ругательство, опционально можно выбрать длину
'''
ADMIN_ID = 664863967

check_message = ''
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
        save_user_to_file(message.from_user.id)
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
        remove_user_from_file(message.from_user.id)
        print(f'user {message.from_user.username} removed from database')
        bot.send_message(message.chat.id, "Вы ушли с пути сигма гриндсета! Чтобы не быть ничтожеством, запишитесь на грайнд с помощью /grind")
    else:
        bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")

@bot.message_handler(commands=['swear'])
def swear(message):
    count = None
    arg = message.text.partition(' ')[2]
    if (arg):
        try:
            count = int(arg)
        except ValueError:
            pass

    bot.send_message(message.chat.id, generate_swearline(count))


ADMIN_SHOW_DATABASE     = 'ADMIN_SHOW_DATABASE'
ADMIN_SAVE_DATABASE     = 'ADMIN_SAVE_DATABASE'
ADMIN_GET_CHECK_TIME    = 'ADMIN_GET_CHECK_TIME'
GRIND_CHECK_YES         = 'GRIND_CHECK_YES'
GRIND_CHECK_NO          = 'GRIND_CHECK_NO'
ADMIN_SEND_ALL_YES      = 'ADMIN_SEND_ALL_YES'
ADMIN_SEND_ALL_NO       = 'ADMIN_SEND_ALL_NO'

@bot.message_handler(commands=['admin'], func=lambda m: len(m.text) == len('/admin'))
def admin_control_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton('Сохранить базу данных', callback_data=ADMIN_SAVE_DATABASE)
    item2 = types.InlineKeyboardButton('Показать базу данных', callback_data=ADMIN_SHOW_DATABASE)
    item3 = types.InlineKeyboardButton('Показать время проверки', callback_data=ADMIN_GET_CHECK_TIME)
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, 'Панель администратора', reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_send_all(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    command = message.text.partition(' ')[2]
    command, _, arg = command.partition(' ')
    if command == 'sendall':
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('Да', callback_data=ADMIN_SEND_ALL_YES)
        item2 = types.InlineKeyboardButton('Нет', callback_data=ADMIN_SEND_ALL_NO)
        markup.add(item1, item2)
        global send_all_message
        send_all_message = arg
        bot.send_message(message.chat.id, 'Вы уверены, что хотите отправить сообщение: \"' + send_all_message + '\"', reply_markup=markup)
    if command == 'setmessage':
        global check_message
        check_message = arg
        bot.send_message(message.chat.id, 'Новое сообщение проверки установлено. Вот его текст:\n\'' + check_message + '\'')
    else:
        bot.send_message(message.chat.id, 'Неизвестная команда администратора')

@bot.message_handler(commands=["getuser"])
def answer(message):
    if (message.from_user.id == ADMIN_ID):
        userid = int(message.text.split(maxsplit=1)[1])
        UsrInfo = bot.get_chat_member(userid, userid).user
        bot.send_message(message.chat.id, "Id: " + str(UsrInfo.id) + "\nFirst Name: " + str(UsrInfo.first_name) + "\nLast Name: " + str(UsrInfo.last_name) +
                            "\nUsername: @" + str(UsrInfo.username))

@bot.message_handler(func=lambda m: True)
def random_stoic_quote(message):
    print(f'{message.from_user.username}: {message.text}')
    quote_number = random.randint(0, 1773)
    quote  = linecache.getline('quotes.txt', quote_number * 2 + 1)
    author = linecache.getline('quotes.txt', quote_number * 2 + 2)
    print('ans: ' + quote + author)
    bot.send_message(message.chat.id, quote + author, reply_to_message_id=message.id)

def save_database(path):
    print('Saving the database')

    # backup
    try:
        if os.path.exists(path + '.bak'):
            shutil.rmtree(path + '.bak')
        shutil.copytree(path, path + '.bak')
    except FileNotFoundError:
        print(f'Error: {DATABASE_DIR} not found')

    for key, value in database.items():
        with open(path + '/' + str(key), 'w') as f:
            print(value, file=f)

    print('Successfully saved the database')

def save_user_to_file(userid):
    with open(DATABASE_DIR + '/' + str(userid), 'w') as f:
        print(database[userid], file=f)

def remove_user_from_file(userid):
    os.remove(DATABASE_DIR + '/' + str(userid))

def sigint_handler(sig, frame):
    if input('Do you want to save the database (y/n)').startswith('y'):
        save_database(DATABASE_DIR)
    sys.exit(0)


def grindcheck():
    print('sending the grindchecks')
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton('Да', callback_data=GRIND_CHECK_YES)
    item2 = types.InlineKeyboardButton('Нет', callback_data=GRIND_CHECK_NO)
    markup.add(item1, item2)
    for entry in database:
        if check_message:
            bot.send_message(entry, check_message)
        bot.send_message(entry, 'Гриндил ли ты сегодня?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == GRIND_CHECK_YES:
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id)
            database[call.from_user.id] += 1
            save_user_to_file(call.from_user.id)
            bot.send_message(call.message.chat.id, 'Keep up the grind!')
        elif call.data == GRIND_CHECK_NO:
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id)
            ans = generate_swearline() 
            bot.send_message(call.message.chat.id, ans)
        elif call.data == ADMIN_SAVE_DATABASE:
            save_database(DATABASE_DIR)
            bot.send_message(call.message.chat.id, 'База данных успешно сохранена')
        elif call.data == ADMIN_SHOW_DATABASE:
            users = []
            for userid, data in database.items():
                user_info = bot.get_chat_member(userid, userid).user
                if user_info.username:
                    users.append(f'{user_info.username} ({userid}): {data}')
                else:
                    users.append(f'{user_info.first_name} {user_info.last_name} ({userid}): {data}')
            bot.send_message(call.message.chat.id, '\n'.join(users))
        elif call.data == ADMIN_SEND_ALL_YES:
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, 'Сообщение отправлено')
            print('sending to everyone:', send_all_message)
            for entry in database:
                bot.send_message(entry, send_all_message)
        elif call.data == ADMIN_SEND_ALL_NO:
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, 'Отправка сообщения отменена')
        elif call.data == ADMIN_GET_CHECK_TIME:
            bot.send_message(call.message.chat.id, f'''Время отправки сообщений - {grindcheck_time[0]}:{grindcheck_time[1]}''')
        else:
            print(f'unknown callback: {call.data}')

def main():
    global database
    database = {}
    
    # read the database
    print('Loading the database...')

    try:
        for filename in os.listdir(DATABASE_DIR):
            with open(DATABASE_DIR + '/' + filename) as f:
                database[int(filename)] = int(f.read())
        print('Database loaded successfully:')
        print(database)
    except FileNotFoundError:
        print(f'Error: {DATABASE_DIR} not found')

    signal.signal(signal.SIGINT, sigint_handler)
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while True:
        # проверка гринда каждый день
        global grindcheck_time
        grindcheck_time = (20, 28)

        hour, minute = grindcheck_time[0] - 3, grindcheck_time[1]
        now = datetime.utcnow()
        to = now.replace(hour=hour, minute=minute)
        if now >= to:
            to += timedelta(days=1)
        seconds_to_wait = (to - now).total_seconds()
        print(f'waiting for {seconds_to_wait} seconds')
        sleep(seconds_to_wait)
        grindcheck()

if __name__ == '__main__':
    main()

