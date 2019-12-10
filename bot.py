import telebot
from telebot.types import Message
from watson_api import text_to_speech, speech_to_text

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

    file_id = message.json[file_type]['file_id']
    received_file_path = bot.get_file(file_id).file_path
    # print(received_file_path.split('/')[1])
    filename = received_file_path.split('/')[1]
    with open(PATH_TO_DATA + filename, 'w+b') as file:
        file.write(bot.download_file(received_file_path))
    bot.send_message(message.chat.id, 'Converting to text')
    result, recognized_text = speech_to_text(filename=filename, output_txt_filename=filename.split('.')[0] + '.txt')
    bot.send_message(message.chat.id, recognized_text)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    # print(message.json)
    bot.send_message(message.chat.id, 'Converting to speech')
    audio_file = text_to_speech(text=message.text, output_filename=str(message.message_id) + '.ogg')
    print(audio_file)
    bot.send_voice(message.chat.id, open(PATH_TO_DATA + audio_file, 'rb'))


bot.polling(none_stop=True)
