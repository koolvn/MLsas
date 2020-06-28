if __name__ == '__main__':
    print('This is a bot logic file. It can not be used separately!')

import logging
import watson_api as wtsn
import yandex_api as yndx
import pandas as pd
import re
import os.path as path
from datetime import datetime
from telebot.types import User, Message, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def bot_logic(bot):
    logging.basicConfig(
        filename='bot.log',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    def log(msg: str, log_lvl=20) -> None:
        logging.log(level=log_lvl, msg=msg)

    if not path.exists('tg_users.csv'):
        log('Creating storage...')
        pd.DataFrame(columns=['start_dt', 'id', 'username']).to_csv('tg_users.csv', index=False)

    rus = re.compile('[а-яА-Я]+')  # нужно для проверки языка сообщения.
    Vladimir = 208470137
    bot.send_message(Vladimir, 'Starting...')
    PATH_TO_DATA = './data/'
    default_params = {'lang': 'ru-RU',
                      'voice': 'alena'}
    # Подробнее здесь https://cloud.yandex.ru/docs/speechkit/tts/request

    voices = {'Филипп': 'filipp', 'Омаж': 'omazh', 'Захар': 'zahar', 'Эрмиль': 'ermil',
              'Оксана': 'oksana', 'Женя': 'jane', 'Алёна': 'alena'}
    inv_voices = {v: k for k, v in voices.items()}

    you_can_help = """
    Можешь поддержать проект чеканной монетой или принять участие в разработке
    \nСо Сбербанка на Яндекс\.Деньги без комиссии
    \n[Яндекс\.Деньги: 410014485115217](https://money.yandex.ru/to/410014485115217)
    \nАльфа Банк: 5559 4937 1870 2583
    """

    class BotUser(User):
        def __init__(self, id, is_bot, first_name, **kwargs):
            super().__init__(id, is_bot, first_name)
            self.params = None
            self.start_dt = None
            for key, value in kwargs.items():
                if pd.notna(value):
                    setattr(self, key, value)
            self.check_in_users()

        def check_in_users(self, get_updated=True):
            bot_users = pd.read_csv('tg_users.csv')
            idx = list(bot_users.columns).index('id')
            if self.id in [x[idx] for x in bot_users.itertuples(index=False)]:
                if get_updated:
                    self.params = eval(bot_users.set_index('id').loc[self.id, 'params'])
                return bot_users
            else:
                self.params = default_params
                self.start_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                bot_users = bot_users.append(pd.Series(vars(self)), ignore_index=True)
                bot_users.to_csv('tg_users.csv', index=False)
                log(f'Added: {self.__repr__()}')

        def save_params(self):
            bot_users = self.check_in_users(get_updated=False).set_index('id')
            bot_users.loc[self.id, 'params'] = str(self.params)
            bot_users.to_csv('tg_users.csv')

        def __repr__(self):
            return f'BotUser: @{self.username}, name: {self.first_name}, id:{self.id}'

        def __getitem__(self, item):
            return getattr(self, item)

    # Keyboards
    def default_keyboard():
        keyboard = InlineKeyboardMarkup()
        ssml = InlineKeyboardButton(text='Что такое SSML?',
                                    url='https://cloud.yandex.ru/docs/speechkit/tts/ssml')
        about = InlineKeyboardButton('Расскажи, что умеешь', callback_data='about')
        settings = InlineKeyboardButton('Настройки', callback_data='settings')
        help_ = InlineKeyboardButton('Помощь', callback_data='help')
        keyboard.row_width = 2
        keyboard.add(about, settings, ssml, help_)
        return keyboard

    def settings_keyboard(**kwargs):
        keyboard = InlineKeyboardMarkup()
        if kwargs['from_id'] == Vladimir:
            keyboard.add(InlineKeyboardButton('Bot Log', callback_data='bot_log'))
        keyboard.add(InlineKeyboardButton('Выбрать голос', callback_data='choose_voice'))
        keyboard.add(InlineKeyboardButton('Выбрать язык', callback_data='choose_language'))
        keyboard.row(InlineKeyboardButton('🔙 назад', callback_data='back'))
        return keyboard

    def voices_keyboard():
        keyboard = InlineKeyboardMarkup()
        keyboard.row(*[InlineKeyboardButton(name,
                                            callback_data=f'{name}') for name in
                       ['Филипп', 'Захар', 'Эрмиль']])
        keyboard.row(*[InlineKeyboardButton(name,
                                            callback_data=f'{name}') for name in
                       ['Оксана', 'Женя', 'Алёна', 'Омаж']])
        keyboard.row(InlineKeyboardButton('🔙 назад', callback_data='back_to_settings'))
        return keyboard

    def custom_url_buttons(btn_names: dict):
        keyboard = InlineKeyboardMarkup()
        for btn in btn_names.keys():
            keyboard.add(InlineKeyboardButton(btn, callback_data=btn, url=btn_names[btn]))
        return keyboard

    def help_keyboard():
        keyboard = custom_url_buttons(
            {'Доступные голоса': 'https://cloud.yandex.ru/docs/speechkit/tts/#voices',
             'Описание методов': 'https://cloud.yandex.ru/docs/speechkit/tts/request',
             'Хочу помочь!': 'https://money.yandex.ru/to/410014485115217',
             'Ответы на вопросы': 'https://t.me/kulyashov'})
        keyboard.add(InlineKeyboardButton('🔙 назад', callback_data='back'))
        return keyboard

    def markup_keyboard():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=False)
        keyboard.row('/start', '/help')
        keyboard.row('Настройки')
        # keyboard.row('Скрыть')
        return keyboard

    def remove_keyboard():
        keyboard = ReplyKeyboardRemove()
        return keyboard

    # HANDLERS
    def reply_on_exception(message, exception):
        bot.send_message(chat_id=message.chat.id,
                         text='Кажется у нас проблемы 😢 Попробуй ещё раз. П.С. я не умею озвучивать эмодзи',
                         reply_markup=custom_url_buttons({'Поддержка': 'https://t.me/kulyashov'}))
        bot.send_message(Vladimir,
                         f'There is a problem with this bot.\nException text: {exception}\n'
                         f'User: @{message.from_user.username} id:{message.from_user.id}\n'
                         f'Message: {message.text}'
                         )

    # Commands handlers
    @bot.message_handler(commands=['start'])
    def start_bot(message: Message):
        user = BotUser(link_source=message.text.split()[-1], **vars(message.from_user))
        log(f'/start from {user.__repr__()}\n{message.text}')
        bot.send_message(message.chat.id, f'\nПривет, {user.first_name}!'
                                          f'\nТы можешь отправить мне текстовые или голосовые сообщения',
                         reply_markup=default_keyboard())

    @bot.message_handler(commands=['help'])
    def show_help(message: Message):
        log(f'/help from id: {message.from_user.id}')
        bot.send_message(message.chat.id, f'Бот находится в разработке.\nБудет классно, если ты поможешь 😊',
                         reply_markup=help_keyboard(), disable_web_page_preview=True)

    @bot.message_handler(func=lambda message: message.text == 'Настройки')
    def show_settings(message: Message):
        user = BotUser(**vars(message.from_user))
        bot.send_message(message.chat.id,
                         'Здесь можно поменять некоторые настройки\n'
                         f'Сейчас выбран голос {inv_voices[user.params["voice"]]}',
                         reply_markup=settings_keyboard(from_id=user.id))

    # Message type handlers
    @bot.message_handler(content_types=['audio', 'voice'])
    def handle_audio(message: Message):
        log(f'Received {message.content_type}'
            f' from {message.from_user.first_name}'
            f' @{message.from_user.username}'
            f' ({message.from_user.id})')
        file_type = None
        if message.voice:
            file_type = 'voice'
        elif message.audio:
            file_type = 'audio'
        else:
            log(f'Message type unknown: {message}')

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
        user = BotUser(**vars(message.from_user))
        log(f'Received {message.content_type}'
            f' from {message.from_user.first_name}'
            f' @{message.from_user.username}'
            f' ({message.from_user.id})')

        bot.send_message(message.chat.id, "Записываю...", reply_markup=markup_keyboard())
        bot.send_chat_action(message.from_user.id, 'record_audio')
        try:
            filename = datetime.now().strftime("%d-%b-%H-%M") + '-from-' + str(message.chat.id) + '.ogg'
            if rus.match(message.text):
                audio_file = yndx.text_to_speech(text=message.text,
                                                 output_filename=filename, params=user.params)
            else:
                audio_file = wtsn.text_to_speech(text=message.text,
                                                 output_filename=filename)

            bot.send_voice(message.chat.id, open(PATH_TO_DATA + 'tts_' + audio_file, 'rb'))
        except UnicodeEncodeError as e:
            print('Wrong character in message!\n', e)
            log('Wrong character in message!\n' + str(e), logging.WARNING)
            reply_on_exception(message, e)
        except RuntimeError as e:
            log(str(e), logging.WARNING)
            reply_on_exception(message, e)

    # CALLBACKS
    @bot.callback_query_handler(func=lambda callback: callback.data in voices.keys())
    def change_voice(callback: CallbackQuery):
        user = BotUser(**vars(callback.from_user))
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False,
                                  text=f'Выбран голос: "{callback.data}"')
        log(f'User {callback.from_user.first_name} chooses {voices[callback.data]} voice')
        user.params['voice'] = voices[callback.data]
        if voices[callback.data] == 'jane':
            user.params['emotion'] = 'evil'

        if voices[callback.data] == 'omazh':
            user.params['emotion'] = 'good'

        user.save_params()
        bot.edit_message_text(text=f'Сейчас выбран голос "{inv_voices[user.params["voice"]]}"',
                              chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              reply_markup=voices_keyboard())

        # bot.send_voice(message.chat.id, open(PATH_TO_DATA + f'voice_{voices[message.text]}.ogg', 'rb'))

    @bot.callback_query_handler(func=lambda callback: True)
    def callback_handling(callback: CallbackQuery):
        user = BotUser(**vars(callback.from_user))
        log(f'Callback from {user.__repr__()}:\n{callback.data}')
        if 'hello' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='Здравствуй!')
            bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'hello.ogg', 'rb'))

        elif 'help' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
            try:
                bot.edit_message_text(text=f'Бот находится в разработке.\nБудет классно, если ты поможешь 😊',
                                      chat_id=callback.message.chat.id,
                                      message_id=callback.message.message_id,
                                      reply_markup=help_keyboard())
            except Exception as e:
                log(str(e), logging.WARNING)
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
                                      chat_id=callback.message.chat.id,
                                      message_id=callback.message.message_id,
                                      reply_markup=settings_keyboard(from_id=user.id),
                                      parse_mode='MarkdownV2')
            except Exception as e:
                log(str(e), logging.WARNING)
                bot.send_message(callback.message.chat.id,
                                 text='Здесь можно поменять настройки голоса и произношения',
                                 reply_markup=settings_keyboard(from_id=user.id))
        elif 'bot_log' in callback.data:
            bot.send_document(Vladimir, data=open('bot.log', 'rb'))

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
                                       f'Сейчас выбран голос "{inv_voices[user.params["voice"]]}"',
                                  reply_markup=voices_keyboard())

        elif 'choose_language' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Пока не работает :(')
