import json
import requests


from app import main
from flask import Flask, request, jsonify, redirect,render_template, url_for
from requests import post



import sys

if sys.version_info < (3, 0):  # Pytohn2.x
    from urllib import urlencode
else:  # Python3.x
    from urllib.parse import urlencode

# Идентификатор приложения
client_id = '6622226'
# Пароль приложения
client_secret = 'Ez15xzZ3OMYVopYkyrkX'

baseurl = 'https://oauth.vk.com/'
redirectUri = 'http://127.0.0.1:5000/tokengetter/this'

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        print(str(request))
    print('index called')
    api_auth_url = 'https://oauth.vk.com/authorize'
    app_id = '6622242'
    permissions = 'friends,audio'
    redirect_uri = 'http://127.0.0.1:5000/tokengetter/this'
    display = 'mobile'
    api_version = '5.8'
    auth_url_template = '{0}?client_id={1}&scope={2}&redirect_uri={3}&display={4}&v={5}&response_type=code'
    auth_url = auth_url_template.format(api_auth_url, app_id, permissions, redirect_uri, display, api_version)

    # Если скрипт был вызван без указания параметра "code",
    # то пользователь перенаправляется на страницу запроса доступа
    return redirect(auth_url)




@app.route('/tokengetter/this')
def token_getter(methods=['GET', 'POST']):
    print('tg called')
    if request.method == 'GET':
        api_token_url = 'https://api.vk.com/oauth/token'
        app_id = '6622242'
        client_secret='aKGiMO3i0JmZcBovYjfK'

        print(request.args.get('code'))
        token_url_template = '{0}?client_id={1}&code={2}&client_secret={3}&redirect_uri={4}'
        token_uri = token_url_template.format(api_token_url, app_id, request.args.get('code'),
                                            client_secret, redirectUri)
        #получаем access token с другими данными
        response = requests.get(token_uri)
        print("TA responce: \n")
        print(response.content)
        json_response = response.json()
        access_token = str(json_response['access_token'])

        resp = dict()

        vk_auth = main.Main()
        data = vk_auth.access_via_token(access_token)
        r = json.dumps(data)
        json_data = json.loads(r) #dict
        print(json_data)
        friendJson = json_data['items'] #dict друзей
        photos = []
        photo_ids = []
        names=[]
        for friend in friendJson:
            try:

                photo_ids.append(friend['photo_id'])
                names.append(str(friend['first_name']) + " " + friend['last_name'])



            except KeyError:
                photos.append('https://vk.com/images/camera_200.png')


        urilist = vk_auth.get_photo_uri(",".join(photo_ids)) #returns list [url or list[dicts]]
        print(urilist)
        for it in urilist:
            photos.append(it)


        resp.update({"photos": photos})

        return render_template("index.html", count=json_data['count'], friendIdList=photos)




if __name__ == '__main__':
    # Отладочная информация
    # app.debug = True
    # Запуск веб-сервера с доступом по порту 8000
    app.run(host='127.0.0.1')