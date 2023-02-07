import telebot
from credentials import bot_token
import signal
import sys

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
        bot.send_message(message.from_user.id, "Вы записаны на гринд!")
    else:
        bot.send_message(message.from_user.id, "Вы уже записаны на гринд. Используйте /lose, чтобы отписаться от гринда и стать неудачником")

@bot.message_handler(commands=['lose'])
def lose(message):
    if message.from_user.id in database:
        del database[message.from_user.id]
        print(f'user {message.from_user.username} removed from database')
        bot.send_message(message.from_user.id, "Вы ушли с пути сигма гриндсета! Чтобы не быть ничтожеством, запишитесь на грайнд с помощью /grind")
    else:
        bot.send_message(message.from_user.id, "Вы не записывались на грайнд. Чтобы стать сигмой, используйте /grind")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    print(f'user {message.from_user.username}: {message.text}')
    bot.reply_to(message, message.text[::-1])

def save_database_to_file(sig, frame):
    print('Saving the database to file')
    with open(DATABASE_FILENAME, 'w') as f:
        for entry in database:
            print(entry, file=f)
    print('Successfully saved the database')
    sys.exit(0)

def main():
    global database
    database = {}
    
    # read the database
    print('Loading the database...')
    try:
        with open(DATABASE_FILENAME) as f:
            for line in f:
                database[int(line)] = 0
        print('Database loaded successfully')
        print(database)
    except FileNotFoundError:
        pass

    signal.signal(signal.SIGINT, save_database_to_file)

    bot.infinity_polling()

if __name__ == '__main__':
    main()

