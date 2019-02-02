import requests
import base64
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.util import prompt_for_user_token
import datetime
import base64
import math
import time
from IRCConnector import IRC
from threading import Thread
from Github import Github
import urllib
import os
from zipfile import ZipFile
import sys
import random

TAG_VERSION = 3

jokes = None

with open("jokes.json", "r", encoding="utf-8") as file:
    jokes = json.loads(file.read())



print("INFO: Suche nach neuer Version...")
ghub = Github("chatn0ir07", "spotify-songrequests", TAG_VERSION)
releases = ghub.CheckReleases()
if releases["IsNew"]:
    filename, headers = urllib.request.urlretrieve(releases["Zipball_URL"])
    print("INFO: Neue Version unter %s gespeichert" % filename)
    print("INFO: Entpacke Archiv...")
    os.mkdir("release")
    zp = ZipFile(filename, "r")
    zp.extractall("release")
    os.remove(filename)
    print("INFO: Archiv entpackt, bitte in den \"release\" Ordner navigieren und aktuelle Datei mit der neuen ersetzen")
    input("Mit einem Tastendruck wird das Program beendet")
    sys.exit(0)
else:
    print("INFO: Keine neue Version gefunden (stand: v%s)" % TAG_VERSION)
SPOTIFYUSER = None

temp = None
with open("creds.json", "r") as file:
    temp = json.load(file)
    CLIENT_ID = temp["ID"]
    CLIENT_SECRET = temp["SECRET"]
    SPOTIFYUSER = temp["SpotifyUsername"]
    file.close()



user = prompt_for_user_token(SPOTIFYUSER, "user-read-currently-playing,user-read-playback-state,user-modify-playback-state,playlist-modify-public,playlist-read-private",client_id=CLIENT_ID,client_secret=CLIENT_SECRET,redirect_uri="http://www.chatn0ir.lima-city.de/spotify-requests")
sp = spotipy.Spotify(auth=user)

playlists = sp.current_user_playlists()
tlist = {}
print(">> Welche Playlist soll nach Liedern gespielt werden <<")

while playlists:
    for i, playlist in enumerate(playlists['items']):
        print("%4d %s" % (i + 1 + playlists['offset'], playlist['name']))
        tlist[i+1+playlists['offset']] = playlist["uri"]
    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None

tplay = input(">> ")
try:
    plist = tlist[int(tplay)]
except ValueError:
    print("Bitte eine Zahl angeben!")


WAITLIST = [
]

client = IRC()
client.Login(temp["OAuth"], temp["USER"], temp["Channel"])


def Chat(user, message, channel = None):
    global sp
    if user != temp["USER"]:
        if message[0:1] == "!":
            command = message[1:].split(" ")[0]
            if command == "sr":
                arguments = message.split(" ")
                tmp = arguments[1][0:7]
                if arguments[1][0:7] == "spotify":
                    WAITLIST.append({"track": {"uri": "".join(arguments)}, "Requester": user})
                    client.Say("Spiele das Lied irgendwann mal")
                else:
                    try:
                        result = sp.search("track:{}".format(" ".join(arguments[1:])))
                        if len(result["tracks"]["items"]) > 0:
                            WAITLIST.append({"track": result["tracks"]["items"][0], "Requester": user, "Name":result['tracks']['items'][0]["name"]})
                            client.Say("{} von {} wurde der Wartschlange hinzugefügt!".format(result['tracks']['items'][0]["name"],", ".join([x["name"] for x in result["tracks"]['items'][0]["artists"]])), temp["Channel"])
                            print("{} wurde von {} der Warteschlange hinzugefügt!".format(result["tracks"]["items"][0]["name"], user))
                        else:
                            client.Say("Nichts für '{}' gefunden".format(" ".join(arguments)), temp["Channel"])
                    except spotipy.client.SpotifyException as ex:
                        print("INFO: Spotify API-Token ist abgelaufen, frage neuen an!")
                        user = prompt_for_user_token("chatnoir-de", "user-read-currently-playing,user-read-playback-state,user-modify-playback-state,playlist-modify-public,playlist-read-private",client_id=CLIENT_ID,client_secret=CLIENT_SECRET,redirect_uri="http://www.chatn0ir.lima-city.de/spotify-requests")
                        sp = spotipy.Spotify(auth=user)
                        print("INFO: Spotify API-Token wurde aktualisiert")

            elif command in ["song"]:
                spx = sp.current_user_playing_track()["item"]
                client.Say("/me Aktuell läuft {} von {}".format(spx["name"], ", ".join([x["name"] for x in spx["artists"]])  ))
                client.Say("/me Die nächsten Songs: ")
                for song in WAITLIST[0:3]:
                    client.Say("/me {} von {}".format(song["Name"],", ".join([x["name"] for x in song["track"]["artists"]])))
            elif command == "flachwitz":
                client.Say("/me "+random.choice(jokes["Flachwitze"]))

def test():
    client.GetMessage(Chat)


t = Thread(target=test, args=())
t.start()



LASTSONG = None
NEXTSONG = None
CURRENTSONG = None

def SongHandler():
    global WAITLIST, sp
    try:
        CurrentSong = sp.current_user_playing_track()
        Progress = CurrentSong["progress_ms"]
        End = CurrentSong["item"]["duration_ms"]
        SleepTime = (End - Progress) - 4000
        Skip = True if Progress > End - 4000 and len(WAITLIST) > 0 else False
        if Skip and len(WAITLIST) > 0:
            #sp.start_playback(uris=[WAITLIST[0]["track"]["uri"]])
            sp.start_playback(uris=list([x["track"]["uri"] for x in WAITLIST])[::-1])
            WAITLIST = []
        else:
            if SleepTime < 0 and len(WAITLIST) > 0:
                #sp.start_playback(uris=[WAITLIST[0]["track"]["uri"]])
                sp.start_playback(uris=list([x["track"]["uri"] for x in WAITLIST]))
                print("Spiele {} vorgeschlagen von {}".format(WAITLIST[0]["track"]["name"], WAITLIST[0]["Requester"]))
                #WAITLIST.pop()
                WAITLIST = []
                SongHandler()
            else:
                if CurrentSong["is_playing"] and SleepTime > 0:
                    print("Warte {} Sekunden bis zum Ende des Songs".format(round(SleepTime/1000,2)))
                    time.sleep(SleepTime/1000)
                    SongHandler()
                elif not CurrentSong["is_playing"] and SleepTime < 3000:
                    sp.start_playback(context_uri=plist)
                    sp.shuffle(True)
                    print("Playlist gestartet")

        if len(WAITLIST) == 0:
            if not CurrentSong["is_playing"]:
                sp.start_playback(context_uri=plist)
                sp.shuffle(True)
        #Recall function
        SongHandler()
    except spotipy.client.SpotifyException as ex:
        print("INFO: Spotify API-Token ist abgelaufen, frage neuen an!")
        user = prompt_for_user_token("chatnoir-de", "user-read-currently-playing,user-read-playback-state,user-modify-playback-state,playlist-modify-public,playlist-read-private",client_id=CLIENT_ID,client_secret=CLIENT_SECRET,redirect_uri="http://www.chatn0ir.lima-city.de/spotify-requests")
        sp = spotipy.Spotify(auth=user)
        print("INFO: Spotify API-Token wurde aktualisiert")
        SongHandler()
SongHandler()