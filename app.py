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
ADMIN_ID = 664863967

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

ADMIN_SHOW_DATABASE = 'ADMIN_SHOW_DATABASE'
ADMIN_SAVE_DATABASE = 'ADMIN_SAVE_DATABASE'
GRIND_CHECK_YES     = 'GRIND_CHECK_YES'
GRIND_CHECK_NO      = 'GRIND_CHECK_NO'
ADMIN_SEND_ALL_YES  = 'ADMIN_SEND_ALL_YES'
ADMIN_SEND_ALL_NO   = 'ADMIN_SEND_ALL_NO'

@bot.message_handler(commands=['admin'], func=lambda m: len(m.text) == len('/admin'))
def admin_control_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton('Сохранить базу данных', callback_data=ADMIN_SAVE_DATABASE)
    item2 = types.InlineKeyboardButton('Показать базу данных', callback_data=ADMIN_SHOW_DATABASE)
    markup.add(item1, item2)
    bot.send_message(message.chat.id, 'Панель администратора', reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_send_all(message):
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
def echo_all(message):
    print(f'{message.from_user.username}: {message.text}')
    bot.reply_to(message, message.text[::-1])

def save_database_to_file(path):
    print('Saving the database to file')

    # backup
    try:
        shutil.copyfile(path, path + '.bak')
    except FileNotFoundError:
        pass

    with open(path, 'w') as f:
        for key, value in database.items():
            print(key, value, file=f)
    print('Successfully saved the database')


def sigint_handler(sig, frame):
    save_database_to_file(DATABASE_FILENAME)
    sys.exit(0)


def grindcheck():
    print('sending the grindchecks')
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton('Да', callback_data=GRIND_CHECK_YES)
    item2 = types.InlineKeyboardButton('Нет', callback_data=GRIND_CHECK_NO)
    markup.add(item1, item2)
    for entry in database:
        bot.send_message(entry, 'Гриндил ли ты сегодня?', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == GRIND_CHECK_YES:
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id)
            database[call.from_user.id] += 1
            bot.send_message(call.message.chat.id, 'Так держать!')
        elif call.data == GRIND_CHECK_NO:
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id)
            ans = 'ну ты и пидор говно ебаное блять ничтожество сука а ну быстро возвращайся к гринду ебаная сука уу блять пидарас говна' 
            bot.send_message(call.message.chat.id, ans)
        elif call.data == ADMIN_SAVE_DATABASE:
            save_database_to_file(DATABASE_FILENAME)
            bot.send_message(call.message.chat.id, 'База данных успешно сохранена')
        elif call.data == ADMIN_SHOW_DATABASE:
            users = []
            for userid, data in database.items():
                user_info = bot.get_chat_member(userid, userid).user
                users.append(f'{user_info.username} ({userid}): {data}')
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
        else:
            print(f'unknown callback: {call.data}')

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

    signal.signal(signal.SIGINT, sigint_handler)
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while True:
        # проверка гринда каждый день
        hour, minute = 18, 29
        hour -= 3
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

