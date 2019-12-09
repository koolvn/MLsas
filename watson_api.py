from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

PATH_TO_DATA = './data/'


def text_to_speech(text='Hello world', output_filename='hello_world.wav'):
    auth = IAMAuthenticator("PlkSiy9TLsDCvxHjjLnQ7dqlTkg1IaSynAGmj9AO4nuU")
    tts = TextToSpeechV1(authenticator=auth)
    tts.set_service_url('https://stream-fra.watsonplatform.net/text-to-speech/api')

    with open(PATH_TO_DATA + output_filename, 'wb') as audio_file:
        audio_file.write(
            tts.synthesize(
                text=text,
                voice='en-US_AllisonVoice',
                accept='audio/wav'
            ).get_result().content)


if __name__ == '__main__':
    text_to_speech()
