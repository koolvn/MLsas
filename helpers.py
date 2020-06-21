import pandas as pd

token = '928914414:AAHsTPLisafVFCEuaYTVJ10rYilrzzW4ADc'
# Telegram WebHooks
WEBHOOK_HOST = '212.33.245.52'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './cert/webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './cert/webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(token)


def add_start_user(message):
    """ Записывает данные пользователей, нажавших старт """

    user_details = message.json['from']
    user_details['link_source'] = message.text.split()[1] if len(message.text.split()) > 1 else None
    start_storage = pd.read_csv('tg_users.csv', index_col='index')
    users_list = list(start_storage['id'])
    print('New start click heard\nUser:\n', user_details)

    if 'first_name' not in user_details.keys():
        user_details['first_name'] = None

    if 'last_name' not in user_details.keys():
        user_details['last_name'] = None

    if 'username' not in user_details.keys():
        user_details['username'] = None

    if 'language_code' not in user_details.keys():
        user_details['language_code'] = None

    if 'is_bot' not in user_details.keys():
        user_details['is_bot'] = False

    if 'id' not in user_details.keys():
        user_details['id'] = None

    if message.from_user.id not in users_list:
        try:
            start_storage = start_storage.append(user_details, ignore_index=True)
            start_storage.to_csv('tg_users.csv', index_label='index')

        except Exception as e:
            print(e)
            return 'Ошибка! Не могу записать юзера!'
        return 'New start click was heard'

    else:
        return 'Not a new user clicked start'
