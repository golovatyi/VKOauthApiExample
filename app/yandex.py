# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, redirect
from requests import post

# Метод для кодирования URL как в Python 3, так и в Python 2
import sys

if sys.version_info < (3, 0):  # Pytohn2.x
    from urllib import urlencode
else:  # Python3.x
    from urllib.parse import urlencode

# Идентификатор приложения
client_id = '0f72168d242e4d3084a229bb6006fcec'
# Пароль приложения
client_secret = 'f5a16cecc5074021b616322f188c3a85'
# Адрес сервера Яндекс.OAuth
baseurl = 'https://oauth.yandex.ru/'

app = Flask(__name__)


@app.route('/')
def index():
    if request.args.get('code', False):
        # Если скрипт был вызван с указанием параметра "code" в URL,
        # то выполняется запрос на получение токена
        print(request.args)
        print(request.data)
        data = {
            'grant_type': 'authorization_code',
            'code': request.args.get('code'),
            'client_id': client_id,
            'client_secret': client_secret
        }
        data = urlencode(data)
        # Токен необходимо сохранить для использования в запросах к API Директа
        return jsonify(post(baseurl + "token", data).json())
    else:
        # Если скрипт был вызван без указания параметра "code",
        # то пользователь перенаправляется на страницу запроса доступа
        return redirect(baseurl + "authorize?response_type=code&client_id={}".format(client_id))


if __name__ == '__main__':
    # Отладочная информация
    # app.debug = True
    # Запуск веб-сервера с доступом по порту 8000
    app.run(host='127.0.0.1', port=8000)