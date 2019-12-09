from ibm_watson import TextToSpeechV1, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

PATH_TO_DATA = './data/'


def text_to_speech(text='Hello world', output_filename='hello_world.wav'):
    """ Принимает на вход текст и имя файла, в который будет сохранён результат синтеза
    """
    auth = IAMAuthenticator("PlkSiy9TLsDCvxHjjLnQ7dqlTkg1IaSynAGmj9AO4nuU")
    tts = TextToSpeechV1(authenticator=auth)
    tts.set_service_url('https://stream-fra.watsonplatform.net/text-to-speech/api')

    with open(PATH_TO_DATA + output_filename, 'wb') as audio_file:
        synthesis = tts.synthesize(
            text=text,
            voice='en-US_AllisonVoice',
            accept='audio/wav'
        )
        audio_file.write(synthesis.get_result().content)


def speech_to_text(filename='hello_world.wav'):
    """ Принимает на воход аудиофайл, возвращает объект с результатами и распознанный текст
    """
    auth = IAMAuthenticator('L2iDf0t1uz3jpwbZmxnJElH-cC92n9gYkwVW9Mii9Aac')
    stt = SpeechToTextV1(authenticator=auth)
    stt.set_service_url('https://stream-fra.watsonplatform.net/speech-to-text/api')

    with open(PATH_TO_DATA + filename, 'rb') as input_audio:
        result = stt.recognize(audio=input_audio)
    recognized_text = result.result['results'][0]['alternatives'][0]['transcript']
    return result, recognized_text


if __name__ == '__main__':
    text_to_speech()
