import requests
import json

PATH_TO_DATA = './data/'
TOKEN = 'AQVNwrQZOHMzw0bVvVXR75_p6dY8JeEWe7uVOh3L'


def text_to_speech(text='Hello world', output_filename='hello_world.ogg', params=None):
    """ Принимает на вход текст и имя файла, в который будет сохранён результат синтеза
        так же можно передать любые параметры API Yandex'а в форме словаря
    """
    auth = TOKEN
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    payload = {'lang': 'ru-RU', 'ssml': f'<speak>{text}</speak>', 'voice': 'filipp', 'emotion': 'evil', 'speed': '0.85'}
    if params:
        payload.update(params)

    with requests.post(url,
                       headers={'Authorization': 'Api-Key ' + auth},
                       data=payload, stream=True
                       ) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        with open(PATH_TO_DATA + 'tts_' + output_filename, "wb+") as f:
            f.write(resp.content)

    output_txt_filename = output_filename.split('.')[0] + '.txt'
    with open(PATH_TO_DATA + 'tts_' + output_txt_filename, 'w+') as text_file:
        text_file.write(text)

    return output_filename


def speech_to_text(input_file: str, output_filename: str):
    """ Принимает на вход имя звукового файла, который нужно распознать
        возвращает распознанный текст и файл с именем начинающимся на stt_
    """
    auth = TOKEN
    url = 'https://tts.api.cloud.yandex.net/speech/v1/stt:recognize?topic=general&lang=ru-RU'

    with open(PATH_TO_DATA + input_file, "rb") as f:
        data = f.read()

    with requests.post(url,
                       headers={'Authorization': 'Api-Key ' + auth},
                       data=data, stream=True
                       ) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))
        recognized_text = json.loads(resp.content)['result']
        with open(PATH_TO_DATA + 'stt_' + output_filename, "w+") as f:
            f.write(recognized_text)

    return resp, recognized_text
