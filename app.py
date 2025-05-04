import sys
import time
import aiogram
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNotFound
from aiogram.types import Message, User, CallbackQuery
from typing import Final, List, Set, Tuple
from aiogram.filters import Command
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.types.web_app_info import WebAppInfo

import logging

import credentials
import asyncio
import signal
from datetime import datetime, timedelta, UTC
import swearing
import linecache
import random

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import ffmpeg
import tempfile

import pathlib

import shelve
from database import Userdata

##################### Constants ################################################

HELP_MESSAGE: Final[str] = '''Этот бот позволяет вам встать на путь sigma male grindset и гриндить каждый день.

Команды:
/grind    - записаться на ежедневный грайнд
/progress - проверить собственный прогресс
/lose - уйти с пути сигмы и стать неудачником
/swear <число> - сгенерировать случайное ругательство, опционально можно выбрать длину
/iqtest - тест IQ
'''
ADMIN_ID: Final[int] = 664863967


# required for callback data
class Calldata:
    ADMIN_SHOW_DATABASE: Final[str] = 'ADMIN_SHOW_DATABASE'
    ADMIN_SAVE_DATABASE: Final[str] = 'ADMIN_SAVE_DATABASE'
    ADMIN_GET_CHECK_TIME: Final[str] = 'ADMIN_GET_CHECK_TIME'
    GRIND_CHECK_YES: Final[str] = 'GRIND_CHECK_YES'
    GRIND_CHECK_NO: Final[str] = 'GRIND_CHECK_NO'
    LOSE_YES: Final[str] = 'LOSE_YES'
    LOSE_NO: Final[str] = 'LOSE_NO'


RANKS: Final[List[str]] = ['пикочад', 'наночад', 'микрочад', 'чад', 'килочад', 'мегачад', 'терачад', 'экзачад',
                           'зетачад', 'йотачад', 'богочад', 'дальше просто некуда']
RANK_MARGINS_SET: Final[Set[int]] = {1, 3, 5, 10, 20, 30, 50, 80, 100, 150}

GRINDCHECK_TIME: Final[Tuple[int, int]] = (19, 20)

DATABASE_FILENAME: Final[str] = 'database.db'
EXECUTION_DIR: Final[str] = str(pathlib.Path(__file__).parent.resolve())

DAYS_TIL_DELETION: Final[int] = 30

VIDEO_DURATION_LIMIT: Final[int] = 60
VIDEO_LOAD_LIMIT: Final[int] = 4  # number of requests allowed simultaneously

##################### Globals ##################################################

bot = aiogram.Bot(token=credentials.bot_token)

storage = MemoryStorage()
dp = aiogram.Dispatcher(storage=storage)

video_generation_load = 0

logging.basicConfig(level=logging.INFO)

################################################################################


def clear_reply_markup(message: Message):
    return bot(message.edit_reply_markup())


class States(StatesGroup):
    forward = State()


@dp.message(Command('help'))
async def send_help(message: Message):
    await bot.send_message(message.chat.id, HELP_MESSAGE)


@dp.message(Command('start'))
async def send_welcome(message: Message):
    await bot.send_message(message.chat.id, "Здравствуйте, мои маленькие любители экстремизма!", reply_to_message_id=message.message_id)


@dp.message(Command('grind'))
async def grind(message: Message):
    if str(message.from_user.id) not in database:
        database[str(message.from_user.id)] = Userdata()
        print(f'user {message.from_user.username} added to database')
        await bot.send_message(message.chat.id, "Вы записаны на гринд!")
    else:
        await bot.send_message(message.chat.id, "Вы уже записаны на гринд. Используйте /lose, чтобы отписаться от гринда и стать неудачником")


@dp.message(Command('progress'))
async def check_progress(message: Message):
    if str(message.from_user.id) in database:
        await bot.send_message(message.chat.id, show_progress(message.from_user))
    else:
        await bot.send_message(message.chat.id, "Вы не записывались на гринд. Чтобы стать сигмой, используйте /grind")


@dp.message(Command('lose'))
async def lose(message: Message):
    if str(message.from_user.id) in database:
        builder = InlineKeyboardBuilder()
        builder.button(text='Да', callback_data=Calldata.LOSE_YES)
        builder.button(text='Нет', callback_data=Calldata.LOSE_NO)
        await bot.send_message(message.chat.id, 'Вы точно хотите отписаться от гринда? (Весь прогресс будет потерян)', reply_markup=builder.as_markup())
    else:
        await bot.send_message(message.chat.id, "Вы не записывались на гринд. Чтобы стать сигмой, используйте /grind")


#@dp.message(Command('webapps'))
#async def webapps(message: Message):
#    builder = InlineKeyboardBuilder()
#    builder.button(text='Zrok', web_app=WebAppInfo(
#        url="https://o3cf7jxyst5a.share.zrok.io/"))
#    builder.button(text='Preview', web_app=WebAppInfo(
#        url="https://preview-zov-kombat.postmodernist1848.ru/"))
#    await bot.send_message(message.chat.id, "Web Apps:", reply_markup=builder.as_markup())


@dp.message(Command('swear'))
async def swear(message: Message):
    count = None
    arg = message.text.partition(' ')[2]
    if (arg):
        try:
            count = int(arg)
        except ValueError:
            pass

    await bot.send_message(message.chat.id, swearing.generate_swearline(count))


@dp.message(Command('iqtest'))
async def iqtest(message: Message):
    await bot.send_message(message.chat.id, 'Считаю IQ...')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, f'Твой IQ: {message.from_user.id % 100 + 50}')


@dp.message(F.text == '/admin')
async def admin_control_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    builder = InlineKeyboardBuilder()
    builder.adjust(1)
    builder.button(text='Сохранить базу данных',
                   callback_data=Calldata.ADMIN_SAVE_DATABASE)
    builder.button(text='Показать базу данных',
                   callback_data=Calldata.ADMIN_SHOW_DATABASE)
    builder.button(text='Показать время проверки',
                   callback_data=Calldata.ADMIN_GET_CHECK_TIME)
    await bot.send_message(message.chat.id, 'Панель администратора', reply_markup=builder.as_markup())


@dp.message(Command('admin'))
async def admin_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    command = message.text.partition(' ')[2]
    command, _, arg = command.partition(' ')
    if command == 'forward':
        await state.set_state(States.forward)
        show_name = (arg.strip() != '-n')
        await state.update_data(show_name=show_name)
        s = 'с указанием отправителя' if show_name else 'без указания отправителя'
        await bot.send_message(message.chat.id, f'Отправь мне сообщение для пересылки всем {s} (/cancel для отмены):')

    elif command == 'debuggrindcheck':
        await grindcheck()
    else:
        await bot.send_message(message.chat.id, 'Неизвестная команда администратора')


@dp.message(Command("cancel"), States.forward)
async def cancel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    await state.set_state(None)
    await bot.send_message(message.chat.id, 'Пересылка отменена')


USAGE: Final[str] = 'Usage: /database update <user> [data] | remove <user>'


@dp.message(Command('database'))
async def database_query(message: Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return

    args = message.text.split()
    if len(args) < 2:
        await bot.send_message(message.chat.id, USAGE)
        return
    match args[1]:
        case 'update':
            if len(args) < 3:
                await bot.send_message(message.chat.id, 'Недостаточно аргументов')
                return
            _, _, user, *items = args
            try:
                items = [int(item) for item in items]
            except ValueError:
                await bot.send_message(message.chat.id, 'Все аргументы должны быть целочисленными')
                return
            try:
                database[user] = Userdata(*items)
                await bot.send_message(message.chat.id, f'User id {user}: {database[user]} добавлен в базу данных')
            except TypeError:
                await bot.send_message(message.chat.id, 'Неверные аргументы Userdata')

        case 'remove':
            if len(args) < 3:
                await bot.send_message(message.chat.id, 'Недостаточно аргументов')
                return
            if args[2] in database:
                del database[args[2]]
                await bot.send_message(message.chat.id, f'Пользователь {args[2]} был удален из базы данных')
            else:
                await bot.send_message(message.chat.id, f'User id {args[2]} не найден в базе данных')
        case _:
            await bot.send_message(message.chat.id, 'Неизвестная субкоманда')


@dp.message(Command("getuser"))
async def get_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "У вас нет прав администратора")
        return
    userid = int(message.text.split(maxsplit=1)[1])
    UsrInfo = (await bot.get_chat_member(userid, userid)).user
    await bot.send_message(message.chat.id, "Id: " + str(UsrInfo.id) + "\nFirst Name: " + str(UsrInfo.first_name) + "\nLast Name: " + str(UsrInfo.last_name) +
                           "\nUsername: @" + str(UsrInfo.username))


async def send_sigma_walk_video(message: Message):
    video_path = EXECUTION_DIR + '/' + "patrick_bateman360p.mp4"

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as original_audio_file:
        await bot.download(message.audio.file_id, original_audio_file.name)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp_file:
            inv = ffmpeg.input(video_path, stream_loop="-1")['v']
            ino = ffmpeg.input(original_audio_file.name)['a']
            out = ffmpeg.output(inv, ino, tmp_file.name, vcodec='copy',
                                acodec='copy', shortest=None, t=VIDEO_DURATION_LIMIT)
            ffmpeg.overwrite_output(out).run()

            reply_video = aiogram.types.input_file.FSInputFile(
                tmp_file.name, filename="sigma.mp4")
            await message.reply_video(reply_video)


@dp.message(F.audio)
async def handle_music(message: Message):

    global video_generation_load
    if video_generation_load >= VIDEO_LOAD_LIMIT:
        await bot.send_message(message.chat.id, "Слишком большая нагрузка на бота. Попробуйте позже")
        return

    video_generation_load += 1

    performer = message.audio.performer
    title = message.audio.title
    file_size = message.audio.file_size

    print(f'Processing {title} by {performer}, {
          round(file_size / (1024 * 1024), 2)} MB from {user_to_str(message.from_user)}')

    await bot.send_message(message.chat.id, "Генерирую видео...")
    start_time = time.time()
    try:
        await asyncio.wait_for(send_sigma_walk_video(message), timeout=30)
    except asyncio.TimeoutError:
        await message.reply("Время ожидания истекло")
    except (ffmpeg.Error) as e:
        await message.reply("Не удалось сгенерировать видео")
        print(e)
        await bot.send_message(ADMIN_ID, str(e))
    else:
        print(f'Video for {title} successfully generated. Took {
              round(time.time() - start_time, 2)} seconds')
    finally:
        video_generation_load -= 1


@dp.message(States.forward)
async def forward(message: Message, state: FSMContext):
    data = await state.get_data()

    for entry in database:
        print(entry)
        if data['show_name']:
            await bot(message.forward(entry))
        else:
            await bot(message.copy_to(entry))

    await state.set_state(None)


@dp.message()
async def random_stoic_quote(message: Message):
    if message.text and message.text.lower().startswith('привет'):
        await bot(message.answer('И тебе привет! Используй /help для помощи'))
    else:
        print(f'{message.from_user.username}: {message.text}')
        quote_number = random.randint(0, 1773)
        quote = linecache.getline('quotes.txt', quote_number * 2 + 1)
        author = linecache.getline('quotes.txt', quote_number * 2 + 2)
        print('ans: ' + quote + author)
        await bot(message.answer(quote + author))


def show_progress(user: User):
    days = database[str(user.id)].days

    if user.username:
        status = f"{user.username}: гриндишь на протяжении {days} дней!\n"
    else:
        status = f"{user.first_name} {
            user.last_name}: гриндишь на протяжении {days} дней!\n"

    # TODO: use list elements instead of hardcoded values
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

    status += 'Твое звание: ' + \
        RANKS[rank] + '\n' + progress_bar + '\n' + \
        'Следующее звание: ' + RANKS[rank + 1]
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

    database[user].days_since_last_check += 1
    days_since_last_check = database[user].days_since_last_check
    try:
        if 0 < DAYS_TIL_DELETION - days_since_last_check <= 3:
            print(f'deleting user {user} in {
                  DAYS_TIL_DELETION - days_since_last_check} days')
            await bot.send_message(user, f'''Внимание! Вы не гриндили более {days_since_last_check} дня(день). \
    Мы будем вынуждены удалить вас из базы данных через {DAYS_TIL_DELETION - days_since_last_check} дня(день)''')
        if DAYS_TIL_DELETION <= days_since_last_check:
            await remove_user_with_notification(user)
        else:
            await bot.send_message(user, 'Гриндил ли ты сегодня?', reply_markup=markup)
    except Exception as e:
        print("Exception occured: ", e)
        print(f'User {user} blocked the bot')
        del database[user]
        return


async def grindcheck():
    print('sending the grindchecks')
    builder = InlineKeyboardBuilder()
    builder.button(text='Да', callback_data=GrindCheckAnswer(response=True))
    builder.button(text='Нет', callback_data=GrindCheckAnswer(response=False))
    markup = builder.as_markup()
    await asyncio.gather(*(send_check(entry, markup) for entry in database))


def user_to_str(user: User):
    if user.username:
        return '@' + str(user.username)
    else:
        return user.first_name + ' ' + user.last_name


class GrindCheckAnswer(CallbackData, prefix="grind_check"):
    response: bool


class Lose(CallbackData, prefix="lose"):
    response: bool


@dp.callback_query(GrindCheckAnswer.filter())
async def grindcheck_answer_handler(callback_query: CallbackQuery, callback_data: GrindCheckAnswer):
    if callback_data.response:
        await clear_reply_markup(callback_query.message)
        user: str = str(callback_query.from_user.id)
        if user not in database:
            return

        database[user].days_since_last_check = 0
        database[user].days += 1
        await bot.send_message(callback_query.message.chat.id, 'Keep up the grind!')

        # проверка на достижение нового уровня
        if database[user].days in RANK_MARGINS_SET:
            await bot.send_message(callback_query.message.chat.id,
                                   'Поздравляю, ты достиг нового звания! Используй /progress, чтобы узнать больше')
    else:
        await clear_reply_markup(callback_query.message)
        ans = swearing.generate_swearline()
        await bot.send_message(callback_query.message.chat.id, ans)


@dp.callback_query()
async def callback(call: CallbackQuery):
    if call.message is None:
        # the message may be deleted
        return
    elif call.data == Calldata.ADMIN_SAVE_DATABASE:
        database.sync()
        await bot.send_message(call.message.chat.id, 'База данных успешно сохранена')
    elif call.data == Calldata.ADMIN_SHOW_DATABASE:
        users = []
        for userid, data in database.items():
            try:
                user_info = (await bot.get_chat_member(int(userid), int(userid))).user
            except TelegramNotFound:
                users.append(f'Unknown username ({userid}): {data}')
                continue
            if user_info.username:
                users.append(
                    f'{user_to_str(user_info)} ({userid}): {data}')
        await bot.send_message(call.message.chat.id, 'База данных:\n' + '\n'.join(users))
    elif call.data == Calldata.ADMIN_GET_CHECK_TIME:
        await bot.send_message(call.message.chat.id,
                               f"Время отправки сообщений - {GRINDCHECK_TIME[0]}:{GRINDCHECK_TIME[1]}\n Осталось {secs_until(GRINDCHECK_TIME[0] - 3, GRINDCHECK_TIME[1])} секунд")
    elif call.data == Calldata.LOSE_YES:
        await remove_user_with_notification(str(call.from_user.id))
    elif call.data == Calldata.LOSE_NO:
        await bot.send_message(call.message.chat.id, "Вы остались на верном пути сигма гриндсета")
    else:
        print(f'unknown callback: {call.data}')


def secs_until(hour: int, minute: int) -> int:
    now = datetime.now(UTC)
    to = now.replace(hour=hour, minute=minute)
    if now >= to:
        to += timedelta(days=1)
    seconds_to_wait = int((to - now).total_seconds())
    return seconds_to_wait


async def grindcheck_loop():
    while True:
        # проверка гринда каждый день
        hour, minute = GRINDCHECK_TIME[0] - 3, GRINDCHECK_TIME[1]
        seconds_to_wait = secs_until(hour, minute)
        print(f'Grindcheck in {seconds_to_wait} seconds')
        await asyncio.sleep(seconds_to_wait)
        await grindcheck()


async def save_loop():
    while True:
        hour = 60 * 60
        await asyncio.sleep(hour)
        database.sync()
        print('Database saved')

# calculates left - right where left, right are (hour, minute) tuples


def time_sub(left: Tuple[int, int], right: Tuple[int, int]) -> Tuple[int, int]:
    minutes = (left[0] * 60 + left[1] - (right[0] * 60 + right[1])) % (24 * 60)
    return divmod(minutes, 60)


async def close_before_restarting():
    hour, minute = time_sub(GRINDCHECK_TIME, (0, 30))
    # utc
    seconds_to_wait = secs_until(hour - 3, minute)
    print(f'Stopping application in {seconds_to_wait} seconds')
    await asyncio.sleep(seconds_to_wait)
    # stop_application()


def stop(signum, frame):
    database.close()
    print('database closed')
    sys.exit(1)


async def main():

    global database
    database = shelve.open(EXECUTION_DIR + '/' +
                           DATABASE_FILENAME, writeback=True)

    print(f"Database ({EXECUTION_DIR + '/' + DATABASE_FILENAME}): {{")
    for key, value in database.items():
        print(f'    {key}: {value}')
    print('}')

    task = asyncio.gather(dp.start_polling(bot, handle_signals=False),
                          grindcheck_loop(), save_loop(), close_before_restarting())
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    await task

if __name__ == '__main__':
    asyncio.run(main())
