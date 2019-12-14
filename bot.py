import telebot
from helpers import token, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH, WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV, WEBHOOK_LISTEN, WEBHOOK_PORT, add_start_user
from telebot.types import Message
from telebot import types
import logging
import ssl
from aiohttp import web
import watson_api as wtsn
import yandex_api as yndx
import re

Vladimir = 208470137
PATH_TO_DATA = './data/'

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(token)
app = web.Application()
bot.send_message(Vladimir, 'Starting...')

# Default api params
tts_params = {'lang': 'ru-RU', 'voice': 'filipp', 'emotion': 'evil', 'speed': '0.85'}
stt_params = ['topic=general', 'lang=ru-RU']


# Process webhook calls
async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)


app.router.add_post('/{token}/', handle)


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Bot logic
# --------------------------------------------------------------------------------------------------------------------
# Keyboards

def language_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton('English', callback_data='english'), types.InlineKeyboardButton('Русский', callback_data='russian'))
    keyboard.row(types.InlineKeyboardButton('עברית', callback_data='hebrew'), types.InlineKeyboardButton('Türk', callback_data='turkish'))

    return keyboard


def remove_keyboard():
    keyboard = types.ReplyKeyboardRemove()
    return keyboard


# --------------------------------------------------------------------------------------------------------------------
# HANDLERS

# Commands handlers
@bot.message_handler(commands=['start'])
def start_bot(message: Message):
    add_start_user(message)
    if message.json['from']['language_code'] in ['ru', 'ua', 'br', 'kz']:
        bot.send_voice(message.chat.id,
                       voice=open('./bot_says_hello.ogg', 'rb'))
        bot.send_message(message.chat.id,
                         text=f'\nВыберите язык',
                         reply_markup=language_keyboard())
    elif message.json['from']['language_code'] in ['en', 'us', 'uk', 'eu']:
        bot.send_voice(message.chat.id,
                       voice=open('./bot_says_hello.ogg', 'rb'))
        bot.send_message(message.chat.id,
                         text=f'\nPlease, choose your language',
                         reply_markup=language_keyboard())
    else:
        bot.send_voice(message.chat.id,
                       voice=open('./bot_says_hello.ogg', 'rb'))
        bot.send_message(message.chat.id,
                         text=f'\nChoose your language',
                         reply_markup=language_keyboard())


# Message type handlers
@bot.message_handler(content_types=['audio', 'voice', 'document'])
def handle_audio(message):
    file_type = None
    if message.document:
        file_type = 'document'
    elif message.voice:
        file_type = 'voice'
    elif message.audio:
        file_type = 'audio'
    else:
        print('Message type unknown', message)

    bot.send_message(message.chat.id, 'Converting to text')
    file_id = message.json[file_type]['file_id']
    received_file_path = bot.get_file(file_id).file_path
    filename = received_file_path.split('/')[1]
    with open(PATH_TO_DATA + filename, 'w+b') as file:
        file.write(bot.download_file(received_file_path))

    # result, recognized_text = wtsn.speech_to_text(input_file=filename, output_txt_filename=filename.split('.')[0] + '.txt')
    result, recognized_text = yndx.speech_to_text(input_file=filename, output_filename=filename.split('.')[0] + '.txt')
    if recognized_text:
        bot.send_message(message.chat.id, recognized_text)
    else:
        bot.send_message(message.chat.id, 'You didn\'t say anything!')


# Text handler
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    bot.send_message(message.chat.id, 'Converting to speech')
    rus = re.compile("[а-яА-Я]+")  # нужно для проверки языка сообщения.
    if rus.match(message.text):
        audio_file = yndx.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg', params=tts_params)
    else:
        audio_file = wtsn.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg')
    # audio_file = yndx.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg', params=tts_params)
    bot.send_voice(message.chat.id, open(PATH_TO_DATA + 'tts_' + audio_file, 'rb'))


# Callbacks handler
@bot.callback_query_handler(func=lambda callback: True)
def inline_callback_handling(callback):
    global tts_params, stt_params
    if 'russian' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False)
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id, text="Русский",
                              reply_markup=language_keyboard())
        tts_params = {'lang': 'ru-RU', 'voice': 'filipp', 'emotion': 'good', 'speed': '0.85'}
        stt_params = ['topic=general', 'lang=ru-RU']
    elif 'english' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False)
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id, text="English",
                              reply_markup=language_keyboard())
        tts_params = {'lang': 'en-US', 'voice': 'nick', 'emotion': 'neutral', 'speed': '0.85'}
        stt_params = ['topic=general', 'lang=en-US']
    elif 'hebrew' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text="Temporary unavailable!\nלא זמין זמנית!")

    elif 'turkish' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False)
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id, text="Türk",
                              reply_markup=language_keyboard())
        tts_params = {'lang': 'tr-TR', 'voice': 'erkanyavas', 'emotion': 'neutral', 'speed': '0.8'}
        stt_params = ['topic=general', 'lang=tr-TR']


############################### END OF BOT LOGIC ###################################
####################################################################################

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Build ssl context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Start web-server (aiohttp)
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)
