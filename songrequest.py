# Song Requests (Twitch IRC) via Spotify
# Für http://twitch.tv/mandybimbom

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
                    result = sp.search("track:{}".format(" ".join(arguments[1:])))
                    if len(result["tracks"]["items"]) > 0:
                        WAITLIST.append({"track": result["tracks"]["items"][0], "Requester": user})
                        client.Say("{} von {} wurde der Wartschlange hinzugefügt!".format(result['tracks']['items'][0]["name"],", ".join([x["name"] for x in result["tracks"]['items'][0]["artists"]])), temp["Channel"])
                        print("{} wurde von {} der Warteschlange hinzugefügt!".format(result["tracks"]["items"][0]["name"], user))
                    else:
                        client.Say("Nichts für '{}' gefunden".format(" ".join(arguments)), temp["Channel"])
                    
def test():
    client.GetMessage(Chat)

############################################################################################################
def CLISong(search):
    arguments = search.split(" ")
    result = sp.search("track:{}".format(" ".join(arguments[1:])))
    if len(result["tracks"]["items"]) > 0:
        WAITLIST.append({"track": result["tracks"]["items"][0], "Requester": "Terminal"})
        print("Spiele als nächstes {} von {}".format(result['tracks']['items'][0]["name"],", ".join([x["name"] for x in result["tracks"]['items'][0]["artists"]])), temp["Channel"])
    else:
        print("Nichts für '{}' gefunden".format(" ".join(arguments)), temp["Channel"])
"""
def MainLoop():
    while True:
        se = input("Lied >> ")
        CLISong(se)

ml = Thread(target=MainLoop)
ml.start()
############################################################################################################
"""


t = Thread(target=test, args=())
t.start()



LASTSONG = None
NEXTSONG = None
CURRENTSONG = None




def NextSongHandler():
    global LASTSONG, NEXTSONG, CURRENTSONG, WAITLIST,sp
    try:
        inf = sp.current_user_playing_track()
        progress = inf["progress_ms"]
        end = inf["item"]["duration_ms"]
        if CURRENTSONG is None:
            CURRENTSONG = inf["item"]["name"]

        #if len(WAITLIST) > 0 and inf["item"]["name"] == CURRENTSONG:
        if len(WAITLIST) > 0:
            if progress < end and progress > end-3000:

                sp.start_playback(uris=[WAITLIST[0]["track"]["uri"]])
                print("INFO: Spiele {} gewünscht von {}".format(WAITLIST[0]["track"]["name"], WAITLIST[0]["Requester"]))
                inf = sp.current_user_playing_track()
                progress = inf["progress_ms"]
                end = inf["item"]["duration_ms"]
                WAITLIST.pop(0)
        #elif len(WAITLIST) == 0 and progress > end-3000:
        elif len(WAITLIST) == 0:
            tmp = sp.current_user_playing_track()
            if not tmp["is_playing"]:
                sp.start_playback(context_uri=plist)
                sp.shuffle(True)

        if CURRENTSONG != inf["item"]["name"]:
            CURRENTSONG = inf["item"]["name"]
        
        if progress < end:
            if ((end-progress)/1000) > 4:
                print(">> Warte bis zum Ende des Lieds ({} sec) {}/{}".format(math.floor((end-progress)/1000)-2,math.floor(progress/1000),math.floor(end/1000)))
                time.sleep(((end-progress)/1000)-2)
                NextSongHandler()
            else:
                NextSongHandler()
    except spotipy.client.SpotifyException as ex:
        print("INFO: Spotify API-Token ist abgelaufen, frage neuen an!")
        user = prompt_for_user_token("chatnoir-de", "user-read-currently-playing,user-read-playback-state,user-modify-playback-state,playlist-modify-public,playlist-read-private",client_id=CLIENT_ID,client_secret=CLIENT_SECRET,redirect_uri="http://www.chatn0ir.lima-city.de/spotify-requests")
        sp = spotipy.Spotify(auth=user)
        print("INFO: Spotify API-Token wurde aktualisiert")
        NextSongHandler()
    except Exception as fuck:
        print("KRITISCH: Ein fehler ist aufgetreten: ")
        print(fuck)
        NextSongHandler()
    NextSongHandler()
NextSongHandler()