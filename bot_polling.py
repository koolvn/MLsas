import telebot
from _secret import bot_token
from bot_logic import bot_logic


bot = telebot.TeleBot(bot_token)

_ = bot_logic(bot)

bot.polling(none_stop=True)
