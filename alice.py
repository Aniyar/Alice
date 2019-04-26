# импортируем библиотеки
from flask import Flask, request
import requests
import logging
import json
import math

home_coords = None
work_coords = None
running = False
end_point = None
start_point = None
asked_start_point = False
asked_end_point = False
asked_time = False
time = None

apikey = 'AIzaSyDharzi0W8POu65GsbXwpnibPK-nEVrqMc'

app = Flask(__name__)

# Устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# Создадим словарь, чтобы для каждой сессии общения с навыком хранились
# подсказки, которые видел пользователь.
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)
    logging.info('Response: %r', request.json)
    # Преобразовываем в JSON и возвращаем
    return json.dumps(response)


def handle_dialog(req, res):
    global apikey
    global home_coords, work_coords, end_point, start_point, asked_start_point, asked_end_point, asked_time, time

    user_id = req['session']['user_id']
    sessionStorage[user_id] = {
        'location': [
            "дом",
            "работа",
            "мое местоположение"
        ],
        'time': [
            "сейчас",
            "8",
            "19"
        ]
    }

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        # Заполняем текст ответа

        res['response']['text'] = 'Привет! Откуда едешь'
        asked_start_point = True
        res['response']['buttons'] = get_suggests(user_id, sessionStorage, 'location')
        return

    if asked_start_point:
        if start_point:
            if asked_end_point:
                if end_point:
                    if asked_time:
                        logging.info('ЗАШЕЛ В КОНЕЦ')
                        distance, vectors_list = get_steps(start_point, end_point)
                        wind_sp, wind_dir = get_wind(time, start_point)
                        message = get_comparison(wind_dir, vectors_list)
                        res['response']['text'] = '\nПротяженность маршрута - ' + distance + \
                                                  '\n Скорость ветра - ' + str(wind_sp) + 'м/с' + \
                                                  message
                        time = None
                        end_point = None
                        start_point = None
                        asked_start_point = False
                        asked_end_point = False
                        asked_time = False
                        return
                    else:
                        res = ask_time(res, user_id)
                        asked_time = True
                else:
                    end_point = get_end_point(req, res)
            else:
                res = ask_end_point(res, user_id)
                asked_end_point = True
        else:
            start_point = get_start_point(req, res)

    else:
        res = ask_start_point(res, user_id)
        asked_start_point = True


def ask_end_point(res, user_id):
    res['response']['text'] = 'куда едешь?'
    res['response']['buttons'] = get_suggests(user_id, sessionStorage, 'location')
    return res


def get_end_point(req, res):
    address = req["request"]["original_utterance"]
    if address.lower() in ['дом', 'домой']:
        end_point = home_coords
        return end_point
    elif address.lower() in ['работа', 'на работу']:
        end_point = work_coords
        return res
    try:
        end_point = get_coords(req["request"]["original_utterance"])
        logging.info('end point = ' + end_point)
    except Exception:
        res['response']['text'] = 'Я не могу найти такой адрес, попробуешь ввести снова?'
        return res
    return end_point


def ask_start_point(res, user_id):
    res['response']['text'] = 'Откуда?'
    res['response']['buttons'] = get_suggests(user_id, sessionStorage, 'location')
    return res


def get_start_point(req, res):
    if req["request"]["original_utterance"].lower() in ['мое местоположение', 'отсюда']:
        start_point = get_current()
        return start_point
    try:
        start_point = get_coords(req["request"]["original_utterance"])
        logging.info('end point = ' + start_point)
    except Exception:
        res['response']['text'] = 'Я не могу найти такой адрес, попробуешь ввести снова?'
        return res
    return start_point


def ask_time(res, user_id):
    res['response']['text'] = 'Ко скольки часам поедешь?'
    res['response']['buttons'] = get_suggests(user_id, sessionStorage, 'time')
    return res


def get_time(req, res):
    if req["request"]["original_utterance"].lower() in ['сейчас', 'прямо сейчас']:
        time = 'now'
        return time
    try:
        time = int(req["request"]["original_utterance"])
        if not (-1 < time < 24):
            raise ValueError
    except Exception:
        res['response']['text'] = 'Я еще не умею распознавать такое написание времени:(((( \n ' \
                                  'Введи пожалуйста точный час без лишних символов) \n' \
                                  'Например, 16, 2, 18 и т.д.'
        return res
    return time


# Функция возвращает две подсказки для ответа.
def get_suggests(user_id, storage, group):
    session = storage[user_id]
    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session[group]
    ]
    return suggests


# функция возвращает координаты переданного адреса
def get_coords(address):
    global apikey
    # url variable store url
    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    # get method of requests module
    # return response object
    res_ob = requests.get(url + 'address=' +
                          address + '&key=' + apikey)
    res = res_ob.json()
    crds = res["results"][0]["geometry"]["location"].values()
    return list(crds)


# функция исследует построенный маршрут между точками А и Б и делит их на прямые линии
# замеряется процентная доля каждого "шага" и его направление движения
# возвращается список процентов и векторов
def get_steps(address1, address2):
    global apikey
    url = 'https://maps.googleapis.com/maps/api/directions/json?'
    res = requests.get(url + 'origin=' + address1 +
                       '&destination=' + address2 + '&key=' + apikey)
    res_ob = res.json()
    steps = res_ob["routes"][0]["legs"][0]["steps"]
    lst = []
    all_d = res_ob["routes"][0]["legs"][0]["distance"]["value"]
    for i in range(len(steps)):
        try:
            d = steps[i]["distance"]["value"]
            if i > 0:
                start = steps[i]["start_location"]
            else:
                start = res_ob["routes"][0]["legs"][0]["start_location"]
            if i < len(steps):
                end = steps[i]["end_location"]
            else:
                end = res_ob["routes"][0]["legs"][0]["end_location"]

            dir_vector = (end['lng'] - start['lng'], end['lat'] - start['lat'])
            step = (int((d / all_d) * 100), dir_vector)
            lst.append(step)
        except Exception:
            continue
    return all_d, lst


# функция сравнивает направление ветра и вектор движения на каждом "шаге" из функции get_steps
# возвращает сообщение
def get_comparison(wind_dir, vector_lst):
    card_dirs = {
        'n': (0, 1),
        's': (0, -1),
        'e': (1, 0),
        'w': (0, 1),
        'ne': (1, 1),
        'nw': (-1, 1),
        'se': (1, -1),
        'sw': (-1, -1)
    }
    wind_vector = card_dirs[wind_dir]
    by_wind = 0
    against_wind = 0
    side_wind = 0
    for i in vector_lst:
        ang = angle(wind_vector, i[1])

        if ang <= math.radians(45):
            by_wind += i[0]
        elif math.radians(135) >= ang >= math.radians(45):
            side_wind += i[0]
        else:
            against_wind += i[0]
    return "Вы будете ехать: \n" + str(by_wind) + "% пути " + "по ветру; \n" + \
           str(against_wind) + "% пути " + "против ветра;\n" + str(side_wind) + "% пути " + "с боковым ветром"


# следующие три функции нужны для нахожения угла между векторами
def dotproduct(v1, v2):
    return sum((a * b) for a, b in zip(v1, v2))


def length(v):
    return math.sqrt(dotproduct(v, v))


def angle(v1, v2):
    return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))


def get_current():
    global apikey
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?'
    res = requests.post(url + 'key=' + apikey)
    res_ob = res.json()
    location = res_ob["location"].values()
    return list(location)


def get_address_by_location(loc):
    global apikey
    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    res = requests.get(url + 'latlng=' + str(loc[0]) + ',' + str(loc[1]) + '&key=' + apikey)
    res_ob = res.json()
    address = res_ob["results"][0]["formatted_address"]
    return address


def get_wind(t, pos):
    logging.info(t, pos)
    lat, lng = pos
    headers = {'X-Yandex-API-Key': '8b271d51-7193-4572-bbcd-a63f9de53f51'}
    url = 'https://api.weather.yandex.ru/v1/forecast?'
    res = requests.get(url + 'lat=' + str(lat) + '&lon' + str(lng), headers=headers)
    res_ob = res.json()

    if t == 'now':
        d = res_ob["fact"]
    else:
        d = res_ob["forecasts"][0]["hours"][int(t)]

    wind_speed = d["wind_speed"]
    wind_dir = d["wind_dir"]
    return wind_speed, wind_dir


if __name__ == '__main__':
    app.run()
