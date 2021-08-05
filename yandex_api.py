import requests
import json

from _secret import yandex_token

PATH_TO_DATA = './data/'
API_KEY = yandex_token


def text_to_speech(text='Hello world', output_filename='hello_world.ogg', params=None, auth=API_KEY, save=True):
    """ Принимает на вход текст и имя файла, в который будет сохранён результат синтеза
        так же можно передать любые параметры API Yandex'а в форме словаря
    """
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    payload = {'lang': 'ru-RU',
               'ssml': '<speak>\n' + text + '\n</speak>',
#               'format': 'lpcm',
#               'sampleRateHertz': 8000,
               'voice': 'filipp'}

    if params:
        payload.update(params)

    with requests.post(url,
                       headers={'Authorization': 'Api-Key ' + auth},
                       data=payload, stream=True
                       ) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        with open(PATH_TO_DATA + 'tts_' + output_filename, "wb+") as sound_file:
            sound_file.write(resp.content)

    output_txt_filename = output_filename.split('.')[0] + '.txt'
    if save:
        with open(PATH_TO_DATA + 'tts_' + output_txt_filename, 'w+', encoding='utf-8') as text_file:
            text_file.write(text)

    return output_filename


def speech_to_text(input_file: str, output_filename: str, auth=API_KEY):
    """ Принимает на вход имя звукового файла, который нужно распознать
        возвращает распознанный текст и файл с именем начинающимся на stt_
    """
    url = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'#?topic=general&lang=ru-RU'

    with open(PATH_TO_DATA + input_file, "rb") as f:
        data = f.read()

    with requests.post(url,
                       headers={'Authorization': 'Api-Key ' + auth},
                       data=data, stream=True
                       ) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))
        recognized_text = json.loads(resp.content)['result']
        with open(PATH_TO_DATA + 'stt_' + output_filename, "w+", encoding='utf-8') as f:
            f.write(recognized_text)

    return resp, recognized_text

