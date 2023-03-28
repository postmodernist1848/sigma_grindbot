'''
TODO:
1. Remove a user after n days of no interraction with the bot
2. Farm
'''
import aiogram
from aiogram.types import Message, User
from typing import Final, List, Set, Tuple
import credentials
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from swearing import generate_swearline
import linecache
import random

import shelve
from database import Userdata

##################### Globals ##################################################

HELP_MESSAGE: Final[str] = '''Этот бот позволяет вам встать на путь sigma male grindset и гриндить каждый день.

Команды:
/grind    - записаться на ежедневный грайнд
/progress - проверить собственный прогресс
/lose - уйти с пути сигмы и стать неудачником
/swear <число> - сгенерировать случайное ругательство, опционально можно выбрать длину
/iqtest - тест IQ
'''
ADMIN_ID: Final[int] = 664863967

#required for callback data
class Calldata:
    ADMIN_SHOW_DATABASE  : Final[str] = 'ADMIN_SHOW_DATABASE'
    ADMIN_SAVE_DATABASE  : Final[str] = 'ADMIN_SAVE_DATABASE'
    ADMIN_GET_CHECK_TIME : Final[str] = 'ADMIN_GET_CHECK_TIME'
    GRIND_CHECK_YES      : Final[str] = 'GRIND_CHECK_YES'
    GRIND_CHECK_NO       : Final[str] = 'GRIND_CHECK_NO'
    ADMIN_SEND_ALL_YES   : Final[str] = 'ADMIN_SEND_ALL_YES'
    ADMIN_SEND_ALL_NO    : Final[str] = 'ADMIN_SEND_ALL_NO'
    LOSE_YES             : Final[str] = 'LOSE_YES'
    LOSE_NO              : Final[str] = 'LOSE_NO'

if not credentials.local:
    PROXY_URL: Final[str] = "http://proxy.server:3128"
    bot = aiogram.Bot(token=credentials.bot_token, proxy=PROXY_URL)
else:
    bot = aiogram.Bot(token=credentials.bot_token)

dp = aiogram.Dispatcher(bot)

RANKS: Final[List[str]] = ['пикочад', 'наночад', 'микрочад', 'чад', 'килочад', 'мегачад', 'терачад', 'экзачад',
        'зетачад', 'йотачад', 'богочад', 'дальше просто некуда']
RANK_MARGINS_SET: Final[Set[int]] = {1, 3, 5, 10, 20, 30, 50, 80, 100, 150}

GRINDCHECK_TIME: Final[Tuple[int, int]] = (19, 20)

DATABASE_FILENAME: Final[str] = 'database.db'
database: shelve.Shelf[Userdata] = shelve.open(DATABASE_FILENAME, writeback=True)

DAYS_TIL_DELETION: Final[int] = 20

################################################################################


@dp.message_handler(commands=['help'])
async def send_help(message: Message):
	await bot.send_message(message.chat.id, HELP_MESSAGE)


@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
	await bot.send_message(message.chat.id, "Здравствуйте, мои маленькие любители экстремизма!", reply_to_message_id=message.message_id)


@dp.message_handler(commands=['grind'])
async def grind(message: Message):
    if str(message.from_user.id) not in database:
        database[str(message.from_user.id)] = Userdata()
        print(f'user {message.from_user.username} added to database')
        await bot.send_message(message.chat.id, "Вы записаны на гринд!")
    else:
        await bot.send_message(message.chat.id, "Вы уже записаны на гринд. Используйте /lose, чтобы отписаться от гринда и стать неудачником")


@dp.message_handler(commands=['progress'])
async def check_progress(message: Message):
    if str(message.from_user.id) in database:
        await bot.send_message(message.chat.id, show_progress(message.from_user))
    else:
        await bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")


@dp.message_handler(commands=['lose'])
async def lose(message: Message):
    if str(message.from_user.id) in database:

        markup = aiogram.types.InlineKeyboardMarkup()
        item1 = aiogram.types.InlineKeyboardButton('Да', callback_data=Calldata.LOSE_YES)
        item2 = aiogram.types.InlineKeyboardButton('Нет', callback_data=Calldata.LOSE_NO)
        markup.add(item1, item2)
        await bot.send_message(message.chat.id, 'Вы точно хотите отписаться от гринда? (Весь прогресс будет потерян)', reply_markup=markup)
    else:
        await bot.send_message(message.chat.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")


@dp.message_handler(commands=['swear'])
async def swear(message: Message):
    count = None
    arg = message.text.partition(' ')[2]
    if (arg):
        try:
            count = int(arg)
        except ValueError:
            pass

    await bot.send_message(message.chat.id, generate_swearline(count))

@dp.message_handler(commands=['iqtest'])
async def iqtest(message: Message):
    await bot.send_message(message.chat.id, 'Считаю IQ...')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, f'Твой IQ: {message.from_user.id % 100 + 50}')


@dp.message_handler(aiogram.dispatcher.filters.Text(equals='/admin'), commands=['admin'])
async def admin_control_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    markup = aiogram.types.InlineKeyboardMarkup(row_width=1)
    item1 = aiogram.types.InlineKeyboardButton('Сохранить базу данных', callback_data=Calldata.ADMIN_SAVE_DATABASE)
    item2 = aiogram.types.InlineKeyboardButton('Показать базу данных', callback_data=Calldata.ADMIN_SHOW_DATABASE)
    item3 = aiogram.types.InlineKeyboardButton('Показать время проверки', callback_data=Calldata.ADMIN_GET_CHECK_TIME)
    markup.add(item1, item2, item3)
    await bot.send_message(message.chat.id, 'Панель администратора', reply_markup=markup)


@dp.message_handler(commands=['admin'])
async def admin_send_all(message: Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    command = message.text.partition(' ')[2]
    command, _, arg = command.partition(' ')
    if command == 'sendall':
        markup = aiogram.types.InlineKeyboardMarkup()
        item1 = aiogram.types.InlineKeyboardButton('Да', callback_data=Calldata.ADMIN_SEND_ALL_YES)
        item2 = aiogram.types.InlineKeyboardButton('Нет', callback_data=Calldata.ADMIN_SEND_ALL_NO)
        markup.add(item1, item2)
        global send_all_message
        send_all_message = arg
        await bot.send_message(message.chat.id, 'Вы уверены, что хотите отправить сообщение: \"' + send_all_message + '\"', reply_markup=markup, parse_mode='html')
    elif command == 'debuggrindcheck':
        await grindcheck()
    else:
        await bot.send_message(message.chat.id, 'Неизвестная команда администратора')


@dp.message_handler(commands=["getuser"])
async def answer(message: Message):
    if (message.from_user.id == ADMIN_ID):
        userid = int(message.text.split(maxsplit=1)[1])
        UsrInfo = (await bot.get_chat_member(userid, userid)).user
        await bot.send_message(message.chat.id, "Id: " + str(UsrInfo.id) + "\nFirst Name: " + str(UsrInfo.first_name) + "\nLast Name: " + str(UsrInfo.last_name) +
                            "\nUsername: @" + str(UsrInfo.username))


@dp.message_handler()
async def random_stoic_quote(message: Message):
    if message.text.lower().startswith('привет'):
        await message.answer('И тебе привет! Используй /help для помощи')
    else:
        print(f'{message.from_user.username}: {message.text}')
        quote_number = random.randint(0, 1773)
        quote  = linecache.getline('quotes.txt', quote_number * 2 + 1)
        author = linecache.getline('quotes.txt', quote_number * 2 + 2)
        print('ans: ' + quote + author)
        await message.answer(quote + author)

def stop_application():
    database.close()
    sys.exit(0)


def show_progress(user: User):
    days = database[str(user.id)].days

    if user.username:
        status = f"{user.username}: гриндишь на протяжении {days} дней!\n"
    else:
        status = f"{user.first_name} {user.last_name}: гриндишь на протяжении {days} дней!\n"

    #TODO: use list elements instead of hardcoded values
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


def generate_progress_bar(start: int, current: int, maxvalue: int) -> str:
    length = 20
    filled_count = (current - start) * length // (maxvalue - start)
    return str(start) + ' [' + '■' * filled_count + '□' * (length - filled_count) + '] ' + str(maxvalue)


async def remove_user_with_notification(userid: str):
    del database[userid]
    print(f'user {userid} removed from database')
    await bot.send_message(userid, "Вы ушли с пути сигма гриндсета! Чтобы не быть ничтожеством, запишитесь на грайнд с помощью /grind")


async def send_check(user: str, markup: aiogram.types.InlineKeyboardMarkup):
    await bot.send_message(user, 'Гриндил ли ты сегодня?', reply_markup=markup)
    database[user].days_since_last_check += 1
    days_since_last_check = database[user].days_since_last_check
    if DAYS_TIL_DELETION <= days_since_last_check:
        await remove_user_with_notification(user)
    elif DAYS_TIL_DELETION - days_since_last_check <= 3:
        print(f'deleting user {user} in {DAYS_TIL_DELETION - days_since_last_check} days')
        await bot.send_message(user, f'''Внимание! Вы не гриндили более {DAYS_TIL_DELETION - 3} дней. \
Мы будем вынуждены удалить вас из базы данных через {DAYS_TIL_DELETION - days_since_last_check} дней''')


async def grindcheck():
    print('sending the grindchecks')
    markup = aiogram.types.InlineKeyboardMarkup()
    item1 = aiogram.types.InlineKeyboardButton('Да', callback_data=Calldata.GRIND_CHECK_YES)
    item2 = aiogram.types.InlineKeyboardButton('Нет', callback_data=Calldata.GRIND_CHECK_NO)
    markup.add(item1, item2)
    await asyncio.gather(*(send_check(entry, markup) for entry in database))


@dp.callback_query_handler()
async def callback(call):
    if call.message is None:
        # the message may be deleted
        return
    match call.data:
        case Calldata.GRIND_CHECK_YES:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            user: str = str(call.from_user.id)
            if user not in database:
                return
            database[user].days_since_last_check = 0
            database[user].days += 1
            await bot.send_message(call.message.chat.id, 'Keep up the grind!')

            # проверка на достижение нового уровня
            if database[user].days in RANK_MARGINS_SET:
                await bot.send_message(call.message.chat.id, 'Поздравляю, ты достиг нового звания! Используй /progress, чтобы узнать больше')
        case Calldata.GRIND_CHECK_NO:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            ans = generate_swearline() 
            await bot.send_message(call.message.chat.id, ans)
        case Calldata.ADMIN_SAVE_DATABASE:
            database.sync()
            await bot.send_message(call.message.chat.id, 'База данных успешно сохранена')
        case Calldata.ADMIN_SHOW_DATABASE:
            users = []
            for userid, data in database.items():
                user_info = (await bot.get_chat_member(int(userid), int(userid))).user
                if user_info.username:
                    users.append(f'@{user_info.username} ({userid}): {repr(data)}')
                else:
                    users.append(f'{user_info.first_name} {user_info.last_name} ({userid}): {repr(data)}')
            await bot.send_message(call.message.chat.id, 'База данных:\n' + '\n'.join(users))
        case Calldata.ADMIN_SEND_ALL_YES:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, 'Сообщение отправлено')
            print('sending to everyone:', send_all_message)
            await asyncio.gather(*(bot.send_message(entry, send_all_message, parse_mode='html') for entry in database))
        case Calldata.ADMIN_SEND_ALL_NO:
            await bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, 'Отправка сообщения отменена')
        case Calldata.ADMIN_GET_CHECK_TIME:
            await bot.send_message(call.message.chat.id, f'''Время отправки сообщений - {GRINDCHECK_TIME[0]}:{GRINDCHECK_TIME[1]}''')
        case Calldata.LOSE_YES:
            await call.message.edit_reply_markup()
            await remove_user_with_notification(str(call.from_user.username))
        case Calldata.LOSE_NO:
            await call.message.edit_reply_markup()
            await bot.send_message(call.message.chat.id, "Вы остались на верном пути сигма гриндсета")
        case _:
            print(f'unknown callback: {call.data}')

async def grindcheck_loop():
    while True:
        # проверка гринда каждый день
        hour, minute = GRINDCHECK_TIME[0] - 3, GRINDCHECK_TIME[1]
        now = datetime.utcnow()
        to = now.replace(hour=hour, minute=minute)
        if now >= to:
            to += timedelta(days=1)
        seconds_to_wait = (to - now).total_seconds()
        print(f'waiting for {seconds_to_wait} seconds')
        await asyncio.sleep(seconds_to_wait)
        await grindcheck()

async def save_loop():
    while True:
        hour = 60 * 60
        await asyncio.sleep(hour)
        database.sync()
        print('Database saved')

async def close_before_restarting():
    hour, minute = 15, 50
    now = datetime.utcnow()
    to = now.replace(hour=hour, minute=minute)
    if now >= to:
        to += timedelta(days=1)
    seconds_to_wait = (to - now).total_seconds()
    print(f'closing in {seconds_to_wait} seconds')
    await asyncio.sleep(seconds_to_wait)
    stop_application()

async def main():

    print("Database: {")
    for key, value in database.items():
        print(f'{key}: {value}')
    print('}')

    asyncio.get_running_loop().add_signal_handler(signal.SIGINT, stop_application)
    await asyncio.gather(dp.start_polling(), grindcheck_loop(), save_loop(), close_before_restarting())

if __name__ == '__main__':
    asyncio.run(main())

