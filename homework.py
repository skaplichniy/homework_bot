import requests
import logging
import telegram
import time
from dotenv import load_dotenv
import os
import json

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

PRACTICUM_RETRY_TIME = 300
PRACTICUM_ENDPOINT = 'https://practicum.yandex.ru/api/'\
                     'user_api/homework_statuses/'

PRACTICUM_HOMEWORK_STATUSES = {
    'approved': 'Hooray! Your homework is checked and everything is cool!',
    'reviewing': 'The tutor started to review your homework',
    'rejected': 'Ooooops! There are some mistakes in your homework. Please, fix it'
}

PRACTICUM_HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot, message):
    """Sending message."""
    try:
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except requests.exceptions.RequestException as error:
        logging.exception(error)
        raise Exception('Something wrong with Telegram')


def get_api_answer(url, current_timestamp):
    """Check the API."""
    try:
        payload = {'from_date': current_timestamp}
        homework_statuses = requests.get(
            url, headers=PRACTICUM_HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        logging.exception(error)
        raise Exception('No data from Practicum')

    if homework_statuses.status_code != 200:
        logging.error('Status mistake', homework_statuses)
    try:
        return homework_statuses.json()
    except json.JSONDecodeError as error:
        logging.exception(error)
        raise Exception('Something wrong with the server')


def parse_status(homework):
    """Chech the status"""
    verdict = PRACTICUM_HOMEWORK_STATUSES.get(homework['status'])
    homework_name = homework['homework_name']

    return f'The status has changed: "{homework_name}". {verdict}'


def check_response(response):
    """Check if everything is ok"""
    homeworks = response.get('homeworks')
    for homework in homeworks:
        status = homework.get('status')
        if status in PRACTICUM_HOMEWORK_STATUSES:
            return homeworks
        else:
            logging.error('No status', status)
            raise Exception('No status')
    return homeworks


def main():
    """Bot."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homeworks = get_api_answer(
                PRACTICUM_ENDPOINT, current_timestamp)
            response_result = check_response(new_homeworks)
            if response_result:
                for homework in response_result:
                    status_result = parse_status(homework)
                    send_message(bot, status_result)
            current_timestamp = int(time.time())
            time.sleep(PRACTICUM_RETRY_TIME)
        except Exception as error:
            logging.error(error)
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID, text=f'Something went wrong: {error}'
            )
            time.sleep(PRACTICUM_RETRY_TIME)


if __name__ == '__main__':
    main()
