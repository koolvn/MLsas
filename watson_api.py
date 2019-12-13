from ibm_watson import TextToSpeechV1, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

PATH_TO_DATA = './data/'


def text_to_speech(text='Hello world', output_filename='hello_world.wav'):
    """ Принимает на вход текст и имя файла, в который будет сохранён результат синтеза
    """
    auth = IAMAuthenticator("PlkSiy9TLsDCvxHjjLnQ7dqlTkg1IaSynAGmj9AO4nuU")
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


def speech_to_text(input_file='hello_world.wav', output_txt_filename=None):
    """ Принимает на воход аудиофайл, возвращает объект с результатами и распознанный текст
    """
    auth = IAMAuthenticator('L2iDf0t1uz3jpwbZmxnJElH-cC92n9gYkwVW9Mii9Aac')
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

# if __name__ == '__main__':
# text_to_speech()
# speech_to_text(filename='joke.wav', output_txt_filename='joke.txt')
