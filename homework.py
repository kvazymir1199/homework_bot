from logging.handlers import RotatingFileHandler
from http import HTTPStatus
import requests
import logging
import os
import sys
import telegram
from dotenv import load_dotenv
import time
import exceptions

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=0,
    backupCount=5,
    mode='w'
)

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
previous_status = ''


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logger.info("Starting process sending message")
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as e:
        logger.error(f"Sending message to Telegram error {e}")
        raise exceptions.TelegramSendMessageError(
            f'Cannot send message to chat. Error: '
            f'{e}')
    logger.debug("Message successfully sent")


def get_api_answer(timestamp=0) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            URL,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException as error:
        raise exceptions.EndPointResultError(
            f"EndPoint is not allowed. ERROR{error}"
        )
    if response.status_code != HTTPStatus.OK:
        raise exceptions.BadRequest(
            f'Не удалось получить данные с сервера.'
            f'Ответ сервера{response.status_code}'
        )
    return response.json()


def check_response(response: requests):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logger.error("Api result isnt dict")
        # Вот тут тест не позволяет добавить свое исключение
        raise TypeError("Api возвращает не словарь")
    if 'homeworks' not in response:
        logger.error("Не найден ключ 'homeworks")
        raise exceptions.CheckResponseEmptyKeyHomeworks(
            "key 'homeworks' wasn't found"
        )
    if not isinstance(response.get('homeworks'), list):
        logger.error("Api didnt have list homeworks")
        # Анологично вот здесь
        raise TypeError("Api не передает список homeworks")

    return response.get('homeworks')


def parse_status(homework: dict):
    """Извлекает из информации о домашней работе статус этой работы."""
    status = homework.get('status')

    if status is None:
        raise exceptions.HomeWorkStatusIsEmpty()
    verdict = HOMEWORK_VERDICTS.get(status)
    if verdict is None:
        raise KeyError('Отсутствует статус работы в ответе сервера')

    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise exceptions.HomeWorkNameIsEmpty(
            'Отсутствует имя работы в ответе сервера'
        )

    global previous_status
    if status != previous_status:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    previous_status = status


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            "Some tokens aren't founded."
            f"{TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID}"
            f"Check it. Process is finished"
        )
        sys.exit("Some tokens are missed. Program process stop")
    timestamp = int(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            api_response = get_api_answer(timestamp)
            result = check_response(api_response)
            if len(result) <= 0:
                continue
            message = parse_status(result[0])
            send_message(bot, message)
            if not api_response.get('current_date') is None:
                timestamp = api_response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
