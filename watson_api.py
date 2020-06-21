from ibm_watson import TextToSpeechV1, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from _secret import ibm_token

PATH_TO_DATA = './data/'
API_TOKEN = IAMAuthenticator(ibm_token)


def text_to_speech(text='Hello world', output_filename='hello_world.wav', auth=API_TOKEN):
    """ Принимает на вход текст и имя файла, в который будет сохранён результат синтеза
    """
    tts = TextToSpeechV1(authenticator=auth)
    tts.set_service_url('https://stream-fra.watsonplatform.net/text-to-speech/api')

    with open(PATH_TO_DATA + 'tts_' + output_filename, 'wb') as audio_file:
        synthesis = tts.synthesize(
            text=text,
            voice='en-US_AllisonV3Voice',  # 'en-US_AllisonVoice',
            accept='audio/wav'
        )
        audio_file.write(synthesis.get_result().content)
    output_txt_filename = output_filename.split('.')[0] + '.txt'
    with open(PATH_TO_DATA + 'tts_' + output_txt_filename, 'w+') as text_file:
        text_file.write(text)

    return output_filename


def speech_to_text(input_file='hello_world.wav', output_txt_filename=None, auth=API_TOKEN):
    """ Принимает на воход аудиофайл, возвращает объект с результатами и распознанный текст
    """

    stt = SpeechToTextV1(authenticator=auth)
    stt.set_service_url('https://stream-fra.watsonplatform.net/speech-to-text/api')

    with open(PATH_TO_DATA + input_file, 'rb') as input_audio:
        result = stt.recognize(audio=input_audio)

    if len(result.result['results']) != 0:
        recognized_text = result.result['results'][0]['alternatives'][0]['transcript']
        if output_txt_filename:
            with open(PATH_TO_DATA + 'stt_' + output_txt_filename, 'w+') as text_file:
                text_file.write(recognized_text)

        with open(PATH_TO_DATA + input_file.split('.')[0] + '.json', 'w+') as json_file:
            json_file.write(str(result))
    else:
        recognized_text = ''
        with open(PATH_TO_DATA + 'empty_stt_' + output_txt_filename, 'w+') as text_file:
            text_file.write(recognized_text)

    return result, recognized_text
