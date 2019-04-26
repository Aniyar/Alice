
import requests
import logging
import json

apikey = 'AIzaSyDharzi0W8POu65GsbXwpnibPK-nEVrqMc'




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

print(get_coords('бейбитшилик,1'))