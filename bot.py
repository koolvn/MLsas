import telebot
# from telebot.types import Message
import watson_api as wtsn
import yandex_api as yndx
import re

rus = re.compile("[а-яА-Я]+")  # нужно для проверки языка сообщения.

bot = telebot.TeleBot('928914414:AAHsTPLisafVFCEuaYTVJ10rYilrzzW4ADc')
Vladimir = 208470137
PATH_TO_DATA = './data/'

bot.send_message(Vladimir, 'Starting...')


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
        print(message)

    bot.send_message(message.chat.id, 'Converting to text')
    file_id = message.json[file_type]['file_id']
    received_file_path = bot.get_file(file_id).file_path
    filename = received_file_path.split('/')[1]

    with open(PATH_TO_DATA + filename, 'w+b') as file:
        file.write(bot.download_file(received_file_path))

    result, recognized_text = wtsn.speech_to_text(filename=filename, output_txt_filename=filename.split('.')[0] + '.txt')

    if recognized_text:
        bot.send_message(message.chat.id, recognized_text)
    else:
        bot.send_message(message.chat.id, 'You didn\'t say anything!')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    bot.send_message(message.chat.id, 'Converting to speech')
    if rus.match(message.text):
        audio_file = yndx.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg', output_path=PATH_TO_DATA)
    else:
        audio_file = wtsn.text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg')

    bot.send_voice(message.chat.id, open(PATH_TO_DATA + 'tts_' + audio_file, 'rb'))


bot.polling(none_stop=True)
