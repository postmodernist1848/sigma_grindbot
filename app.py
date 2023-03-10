'''
TODO:
    1. Rewrite in aiogram + make sending messages asynchronous
    2. Contains globals
    3. Type everything
'''

import aiogram
import credentials
import asyncio
import signal
import sys
import os
from datetime import datetime, timedelta
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

PROXY_URL = "http://proxy.server:3128"
bot = aiogram.Bot(token=credentials.bot_token, proxy=PROXY_URL)
dp = aiogram.Dispatcher(bot)

@dp.message_handler(commands=['help'])
async def send_help(message):
	await bot.send_message(message.chat.id, HELP_MESSAGE)


@dp.message_handler(commands=['start'])
async def send_welcome(message):
	await bot.send_message(message.chat.id, "Здравствуйте, мои маленькие любители экстремизма!", reply_to_message_id=message.message_id)


@dp.message_handler(commands=['grind'])
async def grind(message):
    if message.from_user.id not in database:
        database[message.from_user.id] = 0
        save_user_to_file(message.from_user.id)
        print(f'user {message.from_user.username} added to database')
        await bot.send_message(message.chat.id, "Вы записаны на гринд!")
    else:
        await bot.send_message(message.chat.id, "Вы уже записаны на гринд. Используйте /lose, чтобы отписаться от гринда и стать неудачником")


@dp.message_handler(commands=['progress'])
async def check_progress(message):
    if message.from_user.id in database:
        await bot.send_message(message.chat.id, show_progress(message.from_user))
    else:
        await bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")


@dp.message_handler(commands=['lose'])
async def lose(message):
    if message.from_user.id in database:
        del database[message.from_user.id]
        remove_user_from_file(message.from_user.id)
        print(f'user {message.from_user.username} removed from database')
        await bot.send_message(message.chat.id, "Вы ушли с пути сигма гриндсета! Чтобы не быть ничтожеством, запишитесь на грайнд с помощью /grind")
    else:
        await bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")


@dp.message_handler(commands=['swear'])
async def swear(message):
    count = None
    arg = message.text.partition(' ')[2]
    if (arg):
        try:
            count = int(arg)
        except ValueError:
            pass

    await bot.send_message(message.chat.id, generate_swearline(count))


ADMIN_SHOW_DATABASE     = 'ADMIN_SHOW_DATABASE'
ADMIN_SAVE_DATABASE     = 'ADMIN_SAVE_DATABASE'
ADMIN_GET_CHECK_TIME    = 'ADMIN_GET_CHECK_TIME'
GRIND_CHECK_YES         = 'GRIND_CHECK_YES'
GRIND_CHECK_NO          = 'GRIND_CHECK_NO'
ADMIN_SEND_ALL_YES      = 'ADMIN_SEND_ALL_YES'
ADMIN_SEND_ALL_NO       = 'ADMIN_SEND_ALL_NO'


@dp.message_handler(aiogram.dispatcher.filters.Text(equals='/admin'), commands=['admin'])
async def admin_control_panel(message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
    item1 = aiogram.types.InlineKeyboardButton('Сохранить базу данных', callback_data=ADMIN_SAVE_DATABASE)
    item2 = aiogram.types.InlineKeyboardButton('Показать базу данных', callback_data=ADMIN_SHOW_DATABASE)
    item3 = aiogram.types.InlineKeyboardButton('Показать время проверки', callback_data=ADMIN_GET_CHECK_TIME)
    markup.add(item1, item2, item3)
    await bot.send_message(message.chat.id, 'Панель администратора', reply_markup=markup)


@dp.message_handler(commands=['admin'])
async def admin_send_all(message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    command = message.text.partition(' ')[2]
    command, _, arg = command.partition(' ')
    if command == 'sendall':
        markup = aiogram.types.InlineKeyboardMarkup()
        item1 = aiogram.types.InlineKeyboardButton('Да', callback_data=ADMIN_SEND_ALL_YES)
        item2 = aiogram.types.InlineKeyboardButton('Нет', callback_data=ADMIN_SEND_ALL_NO)
        markup.add(item1, item2)
        global send_all_message
        send_all_message = arg
        await bot.send_message(message.chat.id, 'Вы уверены, что хотите отправить сообщение: \"' + send_all_message + '\"', reply_markup=markup, parse_mode='html')
    elif command == 'setmessage':
        global check_message
        check_message = arg
        await bot.send_message(message.chat.id, 'Новое сообщение проверки установлено. Вот его текст:\n\'' + check_message + '\'')
    elif command == 'debuggrindcheck':
        await grindcheck()
    else:
        await bot.send_message(message.chat.id, 'Неизвестная команда администратора')


@dp.message_handler(commands=["getuser"])
async def answer(message):
    if (message.from_user.id == ADMIN_ID):
        userid = int(message.text.split(maxsplit=1)[1])
        UsrInfo = (await bot.get_chat_member(userid, userid)).user
        await bot.send_message(message.chat.id, "Id: " + str(UsrInfo.id) + "\nFirst Name: " + str(UsrInfo.first_name) + "\nLast Name: " + str(UsrInfo.last_name) +
                            "\nUsername: @" + str(UsrInfo.username))


@dp.message_handler()
async def random_stoic_quote(message):
    if message.text.lower().startswith('привет'):
        await message.answer('И тебе привет! Используй /help для помощи')
    else:
        print(f'{message.from_user.username}: {message.text}')
        quote_number = random.randint(0, 1773)
        quote  = linecache.getline('quotes.txt', quote_number * 2 + 1)
        author = linecache.getline('quotes.txt', quote_number * 2 + 2)
        print('ans: ' + quote + author)
        await message.answer(quote + author)


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


def sigint_handler():
    if input('Do you want to save the database (y/n)').startswith('y'):
        save_database(DATABASE_DIR)
    sys.exit(0)


RANKS = ['пикочад', 'наночад', 'микрочад', 'чад', 'килочад', 'мегачад', 'терачад', 'экзачад',
        'зетачад', 'йотачад', 'богочад', 'дальше просто некуда']
RANK_MARGINS = {1, 3, 5, 10, 20, 30, 50, 80, 100, 150}

def show_progress(user):
    days = database[user.id]

    if user.username:
        status = f"{user.username}: гриндишь на протяжении {days} дней!\n"
    else:
        status = f"{user.first_name} {user.last_name}: гриндишь на протяжении {days} дней!\n"

    if days < 1:
        rank = 0
        progress_bar = generate_progress_bar(0, days, 1)
    elif days < 2:
        rank = 1
        progress_bar = generate_progress_bar(1, days, 3)
    elif days < 5:
        rank = 2
        progress_bar = generate_progress_bar(3, days, 5)
    elif days < 10:
        rank = 3
        progress_bar = generate_progress_bar(5, days, 10)
    elif days < 20:
        rank = 4
        progress_bar = generate_progress_bar(10, days, 20)
    elif days < 30:
        rank = 5
        progress_bar = generate_progress_bar(20, days, 30)
    elif days < 50:
        rank = 6
        progress_bar = generate_progress_bar(30, days, 50)
    elif days < 80:
        rank = 7
        progress_bar = generate_progress_bar(50, days, 80)
    elif days < 100:
        rank = 8
        progress_bar = generate_progress_bar(80, days, 100)
    elif days < 150:
        rank = 9
        progress_bar = generate_progress_bar(100, days, 150)
    else:
        rank = 10
        progress_bar = generate_progress_bar(0, 150, 150)

    status += 'Твое звание: ' + RANKS[rank] + '\n' + progress_bar + '\n' + 'Следующее звание: ' + RANKS[rank + 1]
    return status


def generate_progress_bar(start, current, maxvalue):
    length = 20
    filled_count = (current - start) * length // (maxvalue - start)
    return str(start) + ' [' + '■' * filled_count + '□' * (length - filled_count) + '] ' + str(maxvalue)


async def grindcheck():
    print('sending the grindchecks')
    markup = aiogram.types.InlineKeyboardMarkup()
    item1 = aiogram.types.InlineKeyboardButton('Да', callback_data=GRIND_CHECK_YES)
    item2 = aiogram.types.InlineKeyboardButton('Нет', callback_data=GRIND_CHECK_NO)
    markup.add(item1, item2)
    #TODO: send in parallel
    for entry in database:
        if check_message:
            await bot.send_message(entry, check_message)
        await bot.send_message(entry, 'Гриндил ли ты сегодня?', reply_markup=markup)


@dp.callback_query_handler()
async def callback(call):
    if call.message:
        if call.data == GRIND_CHECK_YES:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            database[call.from_user.id] += 1
            save_user_to_file(call.from_user.id)
            await bot.send_message(call.message.chat.id, 'Keep up the grind!')

            # проверка на достижение нового уровня
            if database[call.from_user.id] in RANK_MARGINS:
                await bot.send_message(call.message.chat.id, 'Поздравляю, ты достиг нового звания! Используй /progress, чтобы узнать больше')

        elif call.data == GRIND_CHECK_NO:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            ans = generate_swearline() 
            await bot.send_message(call.message.chat.id, ans)
        elif call.data == ADMIN_SAVE_DATABASE:
            save_database(DATABASE_DIR)
            await bot.send_message(call.message.chat.id, 'База данных успешно сохранена')
        elif call.data == ADMIN_SHOW_DATABASE:
            users = []
            for userid, data in database.items():
                user_info = (await bot.get_chat_member(userid, userid)).user
                if user_info.username:
                    users.append(f'@{user_info.username} ({userid}): {data}')
                else:
                    users.append(f'{user_info.first_name} {user_info.last_name} ({userid}): {data}')
            await bot.send_message(call.message.chat.id, '\n'.join(users))
        elif call.data == ADMIN_SEND_ALL_YES:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, 'Сообщение отправлено')
            print('sending to everyone:', send_all_message)
            #TODO: send in parallel
            for entry in database:
                await bot.send_message(entry, send_all_message, parse_mode='html')
        elif call.data == ADMIN_SEND_ALL_NO:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, 'Отправка сообщения отменена')
        elif call.data == ADMIN_GET_CHECK_TIME:
            await bot.send_message(call.message.chat.id, f'''Время отправки сообщений - {grindcheck_time[0]}:{grindcheck_time[1]}''')
        else:
            print(f'unknown callback: {call.data}')

async def grindcheck_loop():
    while True:
        # проверка гринда каждый день
        global grindcheck_time
        grindcheck_time = (20, 52)

        hour, minute = grindcheck_time[0] - 3, grindcheck_time[1]
        now = datetime.utcnow()
        to = now.replace(hour=hour, minute=minute)
        if now >= to:
            to += timedelta(days=1)

        seconds_to_wait = (to - now).total_seconds()

        print(f'waiting for {seconds_to_wait} seconds')
        await asyncio.sleep(seconds_to_wait)
        await grindcheck()

async def main():
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

    asyncio.get_running_loop().add_signal_handler(signal.SIGINT, sigint_handler)
    await asyncio.gather(dp.start_polling(), grindcheck_loop())

if __name__ == '__main__':
    asyncio.run(main())

