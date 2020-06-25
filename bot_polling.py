import telebot
from telebot import types
from telebot.types import Message, CallbackQuery, User
import watson_api as wtsn
import yandex_api as yndx
import re

from datetime import datetime

from _secret import bot_token
from helpers import add_start_user

API_TOKEN = bot_token

bot = telebot.TeleBot(API_TOKEN)

# bot.delete_webhook()
#######################################################################
############################# BOT LOGIC ###############################
#######################################################################

rus = re.compile("[а-яА-Я]+")  # нужно для проверки языка сообщения.

Vladimir = 208470137
PATH_TO_DATA = './data/'

default_params = {'lang': 'ru-RU',
                  'voice': 'filipp'}
# Подробнее здесь https://cloud.yandex.ru/docs/speechkit/tts/request
params = None
voices = {'Филипп': 'filipp', 'Омаж': 'omazh', 'Захар': 'zahar', 'Эрмиль': 'ermil',
          'Оксана': 'oksana', 'Женя': 'jane', 'Алёна': 'alena'}
inv_voices = {v: k for k, v in voices.items()}

you_can_help = """
Можешь поддержать проект чеканной монетой или принять участие в разработке
\nСо Сбербанка на Яндекс\.Деньги без комиссии
\n[Яндекс\.Деньги: 410014485115217](https://money.yandex.ru/to/410014485115217)
\nАльфа Банк: 5559 4937 1870 2583
"""
user_list = []
bot.send_message(Vladimir, 'Starting...')


# Keyboards
def default_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_1 = types.InlineKeyboardButton(text='Что такое SSML?',
                                       url='https://cloud.yandex.ru/docs/speechkit/tts/ssml')
    btn_2 = types.InlineKeyboardButton('Расскажи, что умеешь', callback_data='about')
    btn_3 = types.InlineKeyboardButton('Настройки', callback_data='settings')
    btn_4 = types.InlineKeyboardButton('Помощь', callback_data='help')
    keyboard.row_width = 2
    keyboard.add(btn_1, btn_2, btn_3, btn_4)
    return keyboard


def settings_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Выбрать голос', callback_data='choose_voice'))
    keyboard.add(types.InlineKeyboardButton('Выбрать язык', callback_data='choose_language'))
    keyboard.row(types.InlineKeyboardButton('🔙 назад', callback_data='back'))
    return keyboard


def voices_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(*[types.InlineKeyboardButton(name,
                                              callback_data=f'{name}') for name in
                   ['Филипп', 'Захар', 'Эрмиль']])
    keyboard.row(*[types.InlineKeyboardButton(name,
                                              callback_data=f'{name}') for name in
                   ['Оксана', 'Женя', 'Алёна', 'Омаж']])
    keyboard.row(types.InlineKeyboardButton('🔙 назад', callback_data='back_to_settings'))
    return keyboard


def custom_url_buttons(btn_names: dict):
    keyboard = types.InlineKeyboardMarkup()
    for btn in btn_names.keys():
        keyboard.add(types.InlineKeyboardButton(btn, callback_data=btn, url=btn_names[btn]))
    return keyboard


def markup_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                                 one_time_keyboard=False)
    keyboard.row('/start', '/help')
    keyboard.row('Настройки')
    # keyboard.row('Скрыть')
    return keyboard


def remove_keyboard():
    keyboard = types.ReplyKeyboardRemove()
    return keyboard


# HANDLERS
def reply_on_exception(message, exception):
    bot.send_message(chat_id=message.chat.id,
                     text='Кажется у нас проблемы 😢 Попробуй ещё раз. П.С. я не умею озвучивать эмодзи',
                     reply_markup=custom_url_buttons({'Поддержка': 'https://t.me/kulyashov'}))
    bot.send_message(Vladimir,
                     f'User {message.chat.id} had an issue.\nThere is a problem with @ML_pet_bot.\n{exception}')


# Commands handlers
@bot.message_handler(commands=['start'])
def start_bot(message: Message):
    print(f'/start from user: {message.from_user}')
    bot.send_message(message.chat.id, f'\nПривет, {message.chat.first_name}!'
                                      f'\nТы можешь отправить мне текстовые или голосовые сообщения',
                     reply_markup=default_keyboard())
    # TODO: Below methods MUST write to DB! (in order to save and use User's preferences correctly)
    add_start_user(message)
    user_list.append(message.from_user)


@bot.message_handler(commands=['help'])
def show_help(message: Message):
    print(f'/help from id: {message.from_user.id}')
    bot.send_message(message.chat.id, f'Бот находится в разработке.\nБудет классно, если ты поможешь 😊',
                     reply_markup=custom_url_buttons(
                         {'Доступные голоса': 'https://cloud.yandex.ru/docs/speechkit/tts/#voices',
                          'Описание методов': 'https://cloud.yandex.ru/docs/speechkit/tts/request',
                          'Хочу помочь!': 'https://money.yandex.ru/to/410014485115217',
                          'Ответы на вопросы': 'https://t.me/kulyashov'}), disable_web_page_preview=True)


@bot.message_handler(func=lambda message: message.text == 'Настройки')
def show_settings(message: Message):
    bot.send_message(message.chat.id,
                     'Здесь можно поменять некоторые настройки\n'
                     f'Сейчас выбран голос '
                     f'"{inv_voices[params["voice"]] if params else inv_voices[default_params["voice"]]}"'
                     f'\nУ меня много голосов! Выбирай!',
                     reply_markup=settings_keyboard())


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


@bot.message_handler(func=lambda message: message.text != 'Настройки', content_types=['text'])
def handle_text(message: Message):
    print(f'Received {message.content_type}'
          f' from {message.from_user.first_name}'
          f' @{message.from_user.username}'
          f' ({message.from_user.id})')

    bot.send_message(message.chat.id, "Записываю", reply_markup=markup_keyboard())
    bot.send_chat_action(message.from_user.id, 'record_audio')

    try:
        filename = datetime.now().strftime("%d-%b-%H-%M") + '-from-' + str(message.chat.id) + '.ogg'
        if rus.match(message.text):
            audio_file = yndx.text_to_speech(text=message.text,
                                             output_filename=filename, params=params)
        else:
            audio_file = wtsn.text_to_speech(text=message.text,
                                             output_filename=filename)

        bot.send_voice(message.chat.id, open(PATH_TO_DATA + 'tts_' + audio_file, 'rb'))
    except UnicodeEncodeError as e:
        print('Wrong character in message!\n', e)
        reply_on_exception(message, e)
    except RuntimeError as e:
        print(e)
        reply_on_exception(message, e)


# CALLBACKS
@bot.callback_query_handler(func=lambda callback: callback.data in voices.keys())
def change_voice(callback: CallbackQuery):
    bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text=f'Выбран голос: "{callback.data}"')
    print(f'User {callback.from_user.first_name} chooses {voices[callback.data]} voice')
    global params
    params = {'voice': voices[callback.data]}
    bot.edit_message_text(text=f'Сейчас выбран голос '
                               f'"{inv_voices[params["voice"]] if params else inv_voices[default_params["voice"]]}"',
                          chat_id=callback.message.chat.id,
                          message_id=callback.message.message_id,
                          reply_markup=voices_keyboard())
    # bot.send_voice(message.chat.id, open(PATH_TO_DATA + f'voice_{voices[message.text]}.ogg', 'rb'))


@bot.callback_query_handler(func=lambda callback: True)
def callback_handling(callback: CallbackQuery):
    print(f'Callback from {callback.from_user.id}:\n', callback.data)
    if 'btn_1' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='Здравствуй!')
        bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'hello.ogg', 'rb'))

    elif 'help' in callback.data:
        show_help(callback.message)

    elif 'about' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
        bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'what_can_bot_do.ogg', 'rb'))
        # bot.send_video(callback.message.chat.id, open(PATH_TO_DATA + 'thanks.mp4', 'rb'))
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              text=you_can_help,
                              parse_mode='MarkdownV2',
                              disable_web_page_preview=True,
                              reply_markup=default_keyboard())

    elif 'settings' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
        try:
            bot.edit_message_text(text='Здесь можно поменять настройки голоса и произношения',
                                  chat_id=callback.from_user.id,
                                  message_id=callback.message.message_id,
                                  reply_markup=settings_keyboard(),
                                  parse_mode='MarkdownV2')
        except Exception as e:
            print(e)
            bot.send_message(callback.message.chat.id,
                             text='Здесь можно поменять некоторые настройки',
                             reply_markup=settings_keyboard())
    elif 'back' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
        bot.edit_message_text('Рад стараться! Напиши мне или пришли голосовое сообщениие',
                              chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              reply_markup=default_keyboard())
    elif 'choose_voice' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              text='Здесь можно поменять некоторые настройки\n'
                                   f'Сейчас выбран голос '
                                   f'"{inv_voices[params["voice"]] if params else inv_voices[default_params["voice"]]}"',
                              reply_markup=voices_keyboard())
    elif 'choose_language' in callback.data:
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Пока не работает :(')


##################################################################
######################## END OF BOT LOGIC ########################
##################################################################

bot.polling(none_stop=True)
