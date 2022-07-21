import fastf1 as ff1
from fastf1 import plotting
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
import pandas as pd
import os
from datetime import datetime
import requests
import tweepy
from dotenv import load_dotenv

load_dotenv(override=True)
bearer = os.environ.get("Twitter_Bearer")
api_key = os.environ.get("Twitter_API")
api_secret = os.environ.get("Twitter_Secret")
access_token = os.environ.get("Twitter_Access_Token")
access_secret = os.environ.get("Twitter_Access_Secret")
weather_key = os.environ.get("Weather")

plotting.setup_mpl()
ff1.Cache.enable_cache('cache/') 

def twitter_login():
    auth = tweepy.OAuth1UserHandler(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )
    api = tweepy.API(auth)
    return api

def KToC(kelvin):
    return round(kelvin - 273.15)

def weather_forecast(lat, lon):
    req = requests.get(f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={weather_key}")
    daily_weather = req.json()["daily"]
    friday_weather = ""
    saturday_weather = ""
    sunday_weather = ""
    for day in daily_weather:
        weekday = datetime.fromtimestamp(day["dt"]).weekday()
        if weekday == 4: friday_weather = day["weather"][0]["description"].title() + ", " + str(KToC(day["temp"]["day"])) + "°C"
        elif weekday == 5: saturday_weather = day["weather"][0]["description"].title() + ", " + str(KToC(day["temp"]["day"])) + "°C"
        elif weekday == 6: sunday_weather = day["weather"][0]["description"].title() + ", " + str(KToC(day["temp"]["day"])) + "°C"
    return [friday_weather, saturday_weather, sunday_weather]

def getCoords(location):
    data = pd.read_csv('circuits.csv').query(f'location == "{location}"')
    print(data)
    return(data.iloc[0]['lat'], data.iloc[0]['lng'])

def calculate_lap_time(lap):
    days = lap.LapTime.days
    hours, remainder = divmod(lap.LapTime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds += lap.LapTime.microseconds / 1e6
    return (minutes, seconds)

def visualise_lap(track, year, eventName, lap):
    minutes, seconds = calculate_lap_time(lap)
    tel = lap.get_telemetry()
    x = np.array(tel['X'].values)
    y = np.array(tel['Y'].values)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    gear = tel['nGear'].to_numpy().astype(float)
    cmap = plt.get_cmap('Paired')
    lc_comp = LineCollection(segments, norm=plt.Normalize(1, cmap.N + 1), cmap=cmap)
    lc_comp.set_array(gear)
    lc_comp.set_linewidth(5)
    plt.figure(figsize=(9, 9))
    plt.gca().add_collection(lc_comp)
    plt.axis('equal')
    plt.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    cbar = plt.colorbar(mappable=lc_comp, label="Gear", boundaries=np.arange(1, 10))
    cbar.set_ticks(np.arange(1.5, 9.5))
    cbar.set_ticklabels(np.arange(1, 9))
    plt.suptitle(f'{eventName} 2021 - {lap.Driver} - {minutes}:{seconds}')
    plt.text(2000, 5000, "\n".join(str(lap.get_weather_data()).split("\n")[1:8]), style='italic', bbox={
        'facecolor': 'green', 'alpha': 0.5, 'pad': 10})
    weather_data = lap.get_weather_data()
    weather_data.reset_index(drop=True)

    dire = "./brief-graphics/" + track + str(year)
    if not os.path.exists(dire):
        os.makedirs(dire)
    filename = dire + "/GearGraph.png"
    plt.savefig(filename)
    return filename

def tweeter(api, filename, weather, eventName, eventFormat):
    text = "It's " + eventName + (" " + eventFormat if eventFormat == "sprint" else "") + " race week!\nFriday: "+weather[0]+"\nSaturday: "+weather[1]+"\nSunday: "+weather[2]+"\n#F1 #Formula1 #FrenchGP"
    api.update_status_with_media(text, filename=filename)

def load_session(year, track, session):
    session = ff1.get_session(year, track, session)
    weekend = session.event
    return (session, weekend)

year = 2021
track = 'France'
session = 'Q'
session, weekend = load_session(year, track, session)
session.load()

filename = visualise_lap(track, year, weekend.EventName, session.laps.pick_fastest())
lat, lon = getCoords(weekend.Location)
weather = weather_forecast(lat, lon)

year = 2022
session = "R"
session, weekend = load_session(year, track, session)
api = twitter_login()
tweeter(api, filename, weather, weekend.OfficialEventName, weekend.EventFormat)