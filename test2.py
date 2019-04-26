import requests
from main import angle, dotproduct, length
import math
apikey = 'AIzaSyDharzi0W8POu65GsbXwpnibPK-nEVrqMc'


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
            step = (int((d/all_d) * 100), dir_vector)
            lst.append(step)
        except Exception:
            continue
    return lst


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
    return "Вы будете ехать: \n" + str(by_wind) + "% пути " + "по ветру; \n" +\
               str(against_wind) + "% пути " + "против ветра;\n" + str(side_wind) + "% пути " + "с боковым ветром"


def get_current():
    global apikey
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?'
    res = requests.post(url + 'key=' + apikey)
    res_ob = res.json()
    location = res_ob["location"].values()
    return list(location)


# v_lst = get_steps("сыганак,22", "тауелсиздик,11")
# print(v_lst)
# print(get_comparison('n', v_lst))

print(get_current())