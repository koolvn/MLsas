import requests

PATH_TO_DATA = './data/'


def text_to_speech(text='Hello world', output_filename='hello_world.ogg', params=None, output_path=PATH_TO_DATA):
    """ Принимает на вход текст и имя файла, в который будет сохранён результат синтеза
        так же можно передать любые параметры API Yandex'а в форме словаря
    """
    auth = "AQVN0E-Zv9fYT3gJA5Dzq7SkP_FaqP-sMPDvy27u"
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    payload = {'lang': 'ru-RU', 'text': text, 'voice': 'filipp'}
    if params:
        payload.update(params)

    with requests.post(url,
                       headers={'Authorization': 'Api-Key ' + auth},
                       data=payload, stream=True
                       ) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        with open(output_path + 'tts_' + output_filename, "wb+") as f:
            f.write(resp.content)

    output_txt_filename = output_filename.split('.')[0] + '.txt'
    with open(output_path + 'tts_' + output_txt_filename, 'w+') as text_file:
        text_file.write(text)

    return output_filename
