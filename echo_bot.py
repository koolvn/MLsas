import telebot
from _secret import myPy as bot_token
import logging

bot = telebot.TeleBot(bot_token)
logging.basicConfig(
    filename='echo_bot.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def log(msg: str, log_lvl=logging.INFO) -> None:
    logging.log(level=log_lvl, msg=msg)


Vladimir = 208470137
bot.send_message(Vladimir, 'This is ECHO bot... Starting')


@bot.message_handler(commands=['start'])
def start_bot(m: telebot.types.Message):
    log(f'/start from {m.from_user}\n{m.text}')
    bot.send_message(m.chat.id, f'\nПривет, {m.from_user.id}!')


@bot.message_handler(func=lambda message: True)
def echo_all(message: telebot.types.Message):
    bot.send_message(chat_id=message.from_user.id, text=f'Your telegram id:\n{message.from_user.id}')


bot.polling(none_stop=True)
