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
# Не совсем понял, для чего добавлять префиксы? Они ведь и так есть

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot, message):
    """Отправляем сообщение."""
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(url, current_timestamp):
    """Забираем информацию с апи."""
    try:
        payload = {'from_date': current_timestamp}
        homework_statuses = requests.get(url, headers=HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        logging.exception(error)
        raise Exception('Что-то пошло не так')

    if homework_statuses.status_code != 200:
        logging.error('Что-то пошло не так', homework_statuses)
    try:
        return homework_statuses.json()
    except json.JSONDecodeError as error:
        logging.exception(error)
        raise Exception('Что-то пошло не так')


def parse_status(homework):
    """Вытаскиваем статус д/з."""
    verdict = HOMEWORK_STATUSES.get(homework['status'])
    homework_name = homework['homework_name']

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Проверяем всё ли ок."""
    homeworks = response.get('homeworks')
    for homework in homeworks:
        status = homework.get('status')
        if status in HOMEWORK_STATUSES:
            return homeworks
        else:
            logging.error('Нет статуса', status)
            raise Exception('Нет статуса')
    return homeworks


def main():
    """Работа бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    url = ENDPOINT
    while True:
        try:
            new_homeworks = get_api_answer(url, current_timestamp)
            response_result = check_response(new_homeworks)
            if response_result:
                for homework in response_result:
                    status_result = parse_status(homework)
                    send_message(bot, status_result)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.error(error)
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID, text=f'Сбой в работе программы: {error}'
            )
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
