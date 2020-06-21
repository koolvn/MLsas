import telebot
from helpers import token, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH, WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV, WEBHOOK_LISTEN, \
    WEBHOOK_PORT, add_start_user
from telebot.types import Message
import logging
import ssl
from aiohttp import web
import watson_api as wtsn
import yandex_api as yndx
import re

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(token)
app = web.Application()


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

################################# BOT LOGIC #######################################
###################################################################################
rus = re.compile("[а-яА-Я]+")  # нужно для проверки языка сообщения.

Vladimir = 208470137
PATH_TO_DATA = './data/'

bot.send_message(Vladimir, 'Starting...')


# HANDLERS

# Commands handlers
@bot.message_handler(commands=['start'])
def start_bot(message: Message):
    print('New user!')
    print(message.json['from'])
    bot.send_message(message.chat.id, f'\nПривет, {message.chat.first_name}!', reply_markup=default_keyboard(message))
    add_start_user(message)


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


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    print(f'Received:{message}')
    bot.send_message(message.chat.id, 'Converting to speech')
    if rus.match(message.text):
        audio_file = yndx.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg')
    else:
        audio_file = wtsn.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg')

    bot.send_voice(message.chat.id, open(PATH_TO_DATA + 'tts_' + audio_file, 'rb'))


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
