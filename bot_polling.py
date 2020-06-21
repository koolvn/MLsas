import telebot
from telebot import types
from telebot.types import Message, CallbackQuery
import watson_api as wtsn
import yandex_api as yndx
import re

from datetime import datetime

from _secret import bot_token
from helpers import add_start_user

API_TOKEN = bot_token

bot = telebot.TeleBot(API_TOKEN)


# bot.delete_webhook()

############################# BOT LOGIC ###############################

# Keyboards
def default_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_1 = types.InlineKeyboardButton(text='SSML?',
                                       url='https://cloud.yandex.ru/docs/speechkit/tts/ssml')
    btn_2 = types.InlineKeyboardButton('Расскажи, что умеешь', callback_data='btn_2')
    btn_3 = types.InlineKeyboardButton('Настройки', callback_data='btn_3')
    keyboard.row_width = 2
    keyboard.add(btn_1, btn_2, btn_3)
    return keyboard


def markup_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('/start')
    keyboard.row('Что этот бот умеет')
    keyboard.row('Настройки')
    return keyboard


def settings_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Добавить 🚗', callback_data='add_car_for_check'))
    keyboard.add(types.InlineKeyboardButton('Убрать 🚗 из проверки', callback_data='remove_car_from_check'))
    keyboard.row(types.InlineKeyboardButton('Список твоих авто', callback_data='show_user_car_list'))
    return keyboard


def remove_keyboard():
    keyboard = types.ReplyKeyboardRemove()
    return keyboard


rus = re.compile("[а-яА-Я]+")  # нужно для проверки языка сообщения.

Vladimir = 208470137
PATH_TO_DATA = './data/'

bot.send_message(Vladimir, 'Starting...')


# HANDLERS

# Commands handlers
@bot.message_handler(commands=['start'])
def start_bot(message: Message):
    print(f'/start from id: {message.from_user.id}')
    bot.send_message(message.chat.id, f'\nПривет, {message.chat.first_name}!'
                                      f'\nТы можешь отправить мне текстовые или голосовые сообщения',
                     reply_markup=default_keyboard())
    add_start_user(message)


# Message type handlers
@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(message: Message):
    print(f'Received {message.content_type}'
          f' from {message.from_user.first_name}'
          f' @{message.from_user.username}'
          f' ({message.from_user.id})')
    file_type = None
    if message.voice:
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

    result, recognized_text = yndx.speech_to_text(input_file=filename,
                                                  output_filename=filename.split('.')[0] + '.txt')
    if recognized_text:
        bot.send_message(message.chat.id, recognized_text)
    else:
        bot.send_message(message.chat.id, 'You didn\'t say anything!')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    print(f'Received {message.content_type}'
          f' from {message.from_user.first_name}'
          f' @{message.from_user.username}'
          f' ({message.from_user.id})')

    bot.send_message(message.chat.id, 'Converting to speech', reply_markup=markup_keyboard())
    filename = datetime.now().strftime("%d-%b-%H-%M") + '-from-' + str(message.chat.id) + '.ogg'

    if rus.match(message.text):
        audio_file = yndx.text_to_speech(text=message.text,
                                         output_filename=filename)
    else:
        audio_file = wtsn.text_to_speech(text=message.text,
                                         output_filename=filename)

    bot.send_voice(message.chat.id, open(PATH_TO_DATA + 'tts_' + audio_file, 'rb'))


# CALLBACKS
@bot.callback_query_handler(func=lambda callback: True)
def inline_callback_handling(callback: CallbackQuery):
    print('Callback:\n', callback)
    if 'btn_1' in callback.data:
        bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'hello.ogg', 'rb'))
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='Здравствуй!')

    elif 'btn_2' in callback.data:
        bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'what_can_bot_do.ogg', 'rb'))
        # bot.send_video(callback.message.chat.id, open(PATH_TO_DATA + 'thanks.mp4', 'rb'))
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              text='Можешь поддержать проект чеканной монетой.'
                                   '\nСо Сбербанка на Яндекс.Деньги без комиссии ;)'
                                   '\nЯндекс.Деньги: 410014485115217'
                                   '\nАльфа Банк: 5559 4937 1870 2583',
                              reply_markup=default_keyboard())
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')

    elif 'btn_3' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='СЮДА НЕЛЬЗЯ!')


##################################################################
######################## END OF BOT LOGIC ########################
##################################################################

bot.polling()
