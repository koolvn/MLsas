import telebot
from _secret import bot_token
from bot_logic import bot_logic

API_TOKEN = bot_token

bot = telebot.TeleBot(API_TOKEN)

_ = bot_logic(bot)

bot.polling(none_stop=True)
