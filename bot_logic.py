import sqlite3
import logging
import numpy as np
import yandex_api as yndx
import pandas as pd
import cv2
from Darknet import Detector
from datetime import datetime
from telebot.types import User, Message, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

cfg_pth = '/mnt/SSD/ForpostML/Projects/FatigueDetection/Models/FaceDetectorNet/net.cfg'
weights_pth = '/mnt/SSD/ForpostML/Projects/FatigueDetection/Models/FaceDetectorNet/net.weights'
labels_pth = '/mnt/SSD/ForpostML/Projects/FatigueDetection/Models/FaceDetectorNet/net.names'
face_detector = Detector(cfg_pth, weights_pth, labels_pth)

# nn = cv2.dnn.readNetFromTensorflow('/mnt/SSD/ForpostML/tmp/pruned_model.pb')
nn = cv2.dnn.readNetFromONNX('/mnt/SSD/ForpostML/tmp/pruned_simplified.onnx')
#nn= cv2.dnn.readNetFromTensorflow('/mnt/SSD/ForpostML/tmp/cv2_model.pb')
output_layers = nn.getUnconnectedOutLayersNames()
nn.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
nn.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
print('GPU(s) is available' if cv2.cuda.getCudaEnabledDeviceCount()
      else 'No GPU(s) found')


def get_nn_results(image):
    image, faces = face_detector(image, draw_bboxes=False, extend_w_h=(1.1, 1.1))
    results = {}
    cropped_faces = []
    for idx, face in enumerate(faces):
        x, y, w, h, _, _ = face.astype(int)

        face = image[y:y + h, x:x + w]
        cropped_faces.append(face)
        blob = cv2.dnn.blobFromImage(face,
                                     1. / 255.,
                                     (64, 64),
                                     swapRB=True,
                                     crop=False)
        blob = np.transpose(blob, (0, 2, 3, 1))
        nn.setInput(blob)
        #_, proba = nn.forward(output_layers)
        proba = nn.forward(output_layers)[0]
        # print(proba)
        results[f'face {idx + 1}'] = proba.squeeze()
    print(results)
    return image, results, cropped_faces


def post_sql_query(sql_query: str, connection: object, fetch: bool = False) -> str:
    with connection as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql_query)
            conn.commit()
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                return 'Done!'
        except Exception as e:
            logging.log(level=logging.ERROR, msg=f'Database exception!\n{e}')


def bot_logic(bot):
    logging.basicConfig(
        filename='bot.log',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.WARNING)

    def log(msg: str, log_lvl=logging.INFO) -> None:
        logging.log(level=log_lvl, msg=msg)

    Vladimir = 208470137
    bot.send_message(Vladimir, 'Starting...')
    PATH_TO_DATA = './data/'
    default_params = {}

    class BotUser(User):
        def __init__(self, id, is_bot, first_name, **kwargs):
            super().__init__(id, is_bot, first_name)
            self._connection = sqlite3.connect('./data/bot.db')
            self.params = None
            self.start_dt = None
            for key, value in kwargs.items():
                if pd.notna(value):
                    setattr(self, key, value)
            self.check_in_users()

        def check_in_users(self, get_updated=True):
            bot_users = pd.read_sql('select * from users', self._connection)
            idx = list(bot_users.columns).index('id')
            if self.id in [x[idx] for x in bot_users.itertuples(index=False)]:
                if get_updated:
                    self.params = eval(bot_users.set_index('id').loc[self.id, 'params'])
                return bot_users
            else:
                self.params = default_params
                self.start_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                bot_users = bot_users.append(pd.Series(vars(self)).drop('_connection'),
                                             ignore_index=True)
                bot_users.params = bot_users.params.astype(str)
                log(f'{bot_users}', log_lvl=logging.WARNING)
                bot_users.to_sql(name='users', con=self._connection, index=False,
                                 if_exists='replace')
                log(f'Added: {self.__repr__()}', log_lvl=logging.WARNING)

        def save_params(self):
            post_sql_query(f'''UPDATE users SET params = "{self.params}" WHERE id = "{self.id}"''',
                           self._connection, fetch=True)

        def __repr__(self):
            return f'BotUser: @{self.username}, name: {self.first_name}, id:{self.id}'

        def __getitem__(self, item):
            return getattr(self, item)

    # Keyboards
    def default_keyboard():
        keyboard = InlineKeyboardMarkup()
        about = InlineKeyboardButton('Расскажи, что умеешь', callback_data='about')
        # settings = InlineKeyboardButton('Настройки', callback_data='settings')
        # help_ = InlineKeyboardButton('Помощь', callback_data='help')
        keyboard.row_width = 2
        keyboard.add(about)
        return keyboard

    def settings_keyboard(**kwargs):
        keyboard = InlineKeyboardMarkup()
        if kwargs['from_id'] == Vladimir:
            keyboard.add(InlineKeyboardButton('Bot Log', callback_data='bot_log'))
        # keyboard.add(InlineKeyboardButton('Выбрать голос', callback_data='choose_voice'))
        # keyboard.add(InlineKeyboardButton('Выбрать язык', callback_data='choose_language'))
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
            {
                # 'Доступные голоса': 'https://cloud.yandex.ru/docs/speechkit/tts/#voices',
                # 'Описание методов': 'https://cloud.yandex.ru/docs/speechkit/tts/request',
                # 'Хочу помочь!': 'https://money.yandex.ru/to/410014485115217',
                # 'Ответы на вопросы': 'https://t.me/kulyashov'
            })
        keyboard.add(InlineKeyboardButton('🔙 назад', callback_data='back'))
        return keyboard

    def markup_keyboard():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=False)
        keyboard.row('/start', '/help')
        # keyboard.row('Настройки')
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
        user.params.update(default_params)
        log(f'/start from {user.__repr__()}\n{message.text}')
        bot.send_message(message.chat.id, f'\nПривет, {user.first_name}!'
                                          f'\nЭто бот для домашнего задания '
                                          f'"Внедрение DL моделей в Production"\n'
                                          f'Отправь мне фото - получишь результат',
                         reply_markup=default_keyboard())

    @bot.message_handler(commands=['help'])
    def show_help(message: Message):
        log(f'/help from id: {message.from_user.id}')
        bot.send_message(message.chat.id,
                         f'Это бот для домашнего задания "Внедрение в DL моделей в Production"',
                         reply_markup=help_keyboard(), disable_web_page_preview=True)

    # @bot.message_handler(func=lambda message: message.text == 'Настройки')
    # def show_settings(message: Message):
    #     user = BotUser(**vars(message.from_user))
    #     log(f'/settings from id: {message.from_user.id}')
    #     bot.send_message(message.chat.id,
    #                      'Здесь можно поменять некоторые настройки',
    #                      reply_markup=settings_keyboard(from_id=user.id))

    # Message type handlers
    @bot.message_handler(content_types=['photo'])
    def handle_photo(message: Message):
        # print(type(message.document))
        # print(message.document)
        received_file = message.json['photo'][-1]
        # width, height = received_file['width'], received_file['height']
        # print(received_file, '\n', f"width: {width}, height: {height}")
        file_id = received_file['file_id']
        received_file_path = bot.get_file(file_id).file_path
        image_bytes = bot.download_file(received_file_path)
        # print(len(image_bytes))
        image = np.frombuffer(image_bytes, dtype=np.uint8)  # .reshape((height, width, 3))
        image = cv2.imdecode(image, flags=1)
        image, results, cropped_faces = get_nn_results(image)
        bot_answer = '\n'.join([f'{face_idx} - {"Man" if proba < 0.5 else "Woman"} - sigmoid '
                                f'output = {proba: .2f}'
                                for face_idx, proba in results.items()])
        bot_answer = f'Found {len(results)} face(s)\n' + bot_answer
        bot.send_chat_action(message.chat.id, 'upload_photo')
        r = list(results.values())
        for i, face in enumerate(cropped_faces):
            _, bts = cv2.imencode('.webp', face)
            bts = bts.tostring()
            bot.send_photo(message.chat.id, bts, caption=f'{"Man" if r[i] < 0.5 else "Woman"}: {r[i]: .2f} (sigmoid output)',
                       )
        # _, bts = cv2.imencode('.webp', image)
        # bts = bts.tostring()
        # bot.send_photo(message.chat.id, bts, caption=bot_answer,
                       # reply_to_message_id=message.message_id
        #               )
        # bot.send_message(message.chat.id, bot_answer)

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
            log(f'Message type unknown: {message}', log_lvl=logging.WARNING)

        bot.send_message(message.chat.id, 'Converting to text')
        file_id = message.json[file_type]['file_id']
        received_file_path = bot.get_file(file_id).file_path
        filename = received_file_path.split('/')[-1]
        with open(PATH_TO_DATA + filename, 'w+b') as file:
            file.write(bot.download_file(received_file_path))

        result, recognized_text = yndx.speech_to_text(input_file=filename,
                                                      output_filename=filename.split('.')[
                                                                          0] + '.txt')
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
            f' ({message.from_user.id})', log_lvl=logging.WARNING)

        bot.send_message(message.chat.id, "Я ничего не умею делать с текстом, "
                                          "у меня лапки.\nПришли картинку",
                         reply_markup=markup_keyboard())

    # CALLBACKS
    @bot.callback_query_handler(func=lambda callback: True)
    def callback_handling(callback: CallbackQuery):
        user = BotUser(**vars(callback.from_user))
        log(f'Callback from {user.__repr__()}:\n{callback.data}')
        if 'hello' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False,
                                      text='Здравствуй!')
            bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'hello.ogg', 'rb'))

        elif 'help' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
            try:
                bot.edit_message_text(
                    text=f'Бот находится в разработке.\nБудет классно, если ты поможешь 😊',
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=help_keyboard())
            except Exception as e:
                log(str(e), logging.ERROR)
                show_help(callback.message)

        elif 'about' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
            # bot.send_voice(callback.from_user.id, open(PATH_TO_DATA + 'what_can_bot_do.ogg', 'rb'))
            # bot.send_video(callback.message.chat.id, open(PATH_TO_DATA + 'thanks.mp4', 'rb'))
            bot.edit_message_text(chat_id=callback.message.chat.id,
                                  message_id=callback.message.message_id,
                                  text="Этот бот умеет находить лица на фото и определять пол",
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
                log(str(e), logging.ERROR)
                bot.send_message(callback.message.chat.id,
                                 text='Здесь можно поменять настройки голоса и произношения',
                                 reply_markup=settings_keyboard(from_id=user.id))
        elif 'bot_log' in callback.data:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='')
            bot.send_document(Vladimir, data=open('bot.log', 'rb'))
            bot.send_message(Vladimir, text=str(
                pd.read_sql('select * from users', user._connection).to_dict(orient='records')))
            # bot.send_message(Vladimir, text=f"{pd.read_sql('select * from user_msgs',
            #                                             user._connection).to_dict()}")

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
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True,
                                      text='Пока не работает :(')


if __name__ == '__main__':
    print('This is a bot logic file. It can not be used separately!')
