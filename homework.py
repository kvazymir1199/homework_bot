from logging.handlers import RotatingFileHandler
from http import HTTPStatus
import requests
import logging
import os
import sys
import telegram
from dotenv import load_dotenv
import time

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filemode='w'
)
logger = logging.getLogger(__name__)
# Устанавливаем уровень, с которого логи будут сохраняться в файл
logger.setLevel(logging.DEBUG)
# Указываем обработчик логов
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000,
                              backupCount=5)
logger.addHandler(handler)
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN is None:
        error = 'Не указан токен яндекса'
        logging.critical(error)
        return False

    if TELEGRAM_TOKEN is None:
        error = 'Не указан токен бота'
        logging.critical(error)
        return False

    if TELEGRAM_CHAT_ID is None:
        error = 'Не указан адресат'
        logging.critical(error)
        return False

    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as e:
        logging.error(f'Cannot send message to chat. Error: {e}')
    logger.debug("Message was successfully sent")


def get_api_answer(timestamp=0) -> requests:
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            URL,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException:
        logger.error('Error when sending message')
    if response.status_code != HTTPStatus.OK:
        logger.error('EndPoint not ready at this moment!')
        raise requests.RequestException(
            'Не удалось получить данные с сервера.')
    return response.json()


def check_response(response: requests):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logger.error("Api result isnt dict")
        raise TypeError("Api возвращает не словарь")
    if 'homeworks' not in response:
        logger.error("Не найден ключ 'homeworks")
        raise ValueError("key 'homeworks' wasn't found")
    if not isinstance(response.get('homeworks'), list):
        logger.error("Api didnt have list homeworks")
        raise TypeError("Api не передает список homeworks")
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    status = homework['status']
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        verdict = ''
        raise KeyError('Отсутствует статус работы в ответе сервера')

    try:
        homework_name = homework['homework_name']
    except KeyError:
        raise KeyError('Отсутствует имя работы в ответе сервера')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('No tockens')
        sys.exit(1)
    timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            responce = get_api_answer(timestamp)
            result = check_response(responce)
            if len(result) > 0:
                logger.debug('It is new result')
                message = parse_status(result[0])
                send_message(bot, message)
                timestamp = responce['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
