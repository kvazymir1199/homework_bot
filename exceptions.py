class EndPointResultError(Exception):
    """ Ошибка доступа к конечному адресу"""
    pass


class BadRequest(Exception):
    """ Ошибка плохое соединение с сервером"""
    pass


class TelegramSendMessageError(Exception):
    """ Ошибка отправки сообщения в телеграм"""
    pass


class CheckResponseEmptyKeyHomeworks(Exception):
    """ Отсутствует ключ homeworks в словаре response"""
    pass


class HomeWorkStatusIsEmpty(Exception):
    """ В функции parse_status при обращении к словарю homeworks отсутствует
    запрашиваемое значение по ключ status"""
    pass


class HomeWorkNameIsEmpty(Exception):
    """ В функции parse_status при обращении к словарю homeworks отсутствует
    запрашиваемое значение по ключ status"""
    pass


class ResponseApiIsNotDict(TypeError):
    """ Ответ от сервера не является словарем"""
    pass


class ResponseApiDictNotContainListHomeworks(TypeError):
    """ Словарь ответа сервера не содержит вложенного списка 'homeworks'"""
    pass
