#!/usr/bin/env python3
import os
import platform
import datetime
import threading
import json
import re
import requests
color_remove =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')

with open('watch-list.json') as watchlist_json:
    watchlist = json.load(watchlist_json)

def watchNotification(message):
    infodata = {}
    infodata["value1"] = os.uname()[1]
    infodata["value2"] = color_remove.sub("", message);
    requests.post("https://maker.ifttt.com/trigger/watch-alert/with/key/bf0pwzSex_KbKYbJBrl0sG", data=infodata)    

def checkFile(path):
    fileStat = os.stat(path)
    if watchlist[path]["last-modified"] == "None":
       watchlist[path]["last-modified"] = fileStat.st_mtime

    if float(watchlist[path]["last-modified"]) >= fileStat.st_mtime:
        with open(path) as watch_file:
            watchlist[path]["last-content"] = watch_file.read()
    else:
        with open(path) as watch_file:
            print("\u001b[31mA file (" + path + ") has been modified!\n\n\u001b[32mOld content:\n\u001b[37m" + watchlist[path]["last-content"] + "\n\n\u001b[33mNew content:\n\u001b[37m" + watch_file.read())
            watchNotification("A file " + path + " has been modified!\nNew content:\n" + watch_file.read())
            watchNotification("A file " + path + " has been modified!\nOld content:\n" + watchlist[path]["last-content"])

        watchlist[path]["last-modified"] = fileStat.st_mtime

def checkDir(path):
    dirStat = os.stat(path)
    if watchlist[path]["last-modified"] == "None":
       watchlist[path]["last-modified"] = dirStat.st_mtime

    if float(watchlist[path]["last-modified"]) >= dirStat.st_mtime:
        watchlist[path]["last-content"] = ""
        for file in os.listdir(path):
            if os.path.isfile(file):
                watchlist[path]["last-content"] += "   \u001b[0m- " + file + "\n"
            elif os.path.isdir(file):
                watchlist[path]["last-content"] += "   \u001b[0m- \u001b[36m" + file + "\n"
    else:
        files = ""
        for file in os.listdir(path):
            if os.path.isfile(file):
                files += "   \u001b[0m- " + file + "\n"
            elif os.path.isdir(file):
                files += "   \u001b[0m- \u001b[36m" + file + "\n"


        print("\u001b[31mA directory (" + path +") has been modified. \n\n\u001b[32mOld content:\n\u001b[37m" + watchlist[path]["last-content"] + "\n\n\u001b[33mNew content:\n\u001b[37m" + files + "\u001b[0m")
        watchNotification("A directory (" + path +") has been modified.\n\nNew content:\n" + files)
        watchNotification("A directory (" + path +") has been modified.\n\nOld content:\n" + watchlist[path]["last-content"])
        watchlist[path]["last-modified"] = dirStat.st_mtime


def watchListLoop():
    threading.Timer(30.0, watchListLoop).start()
    for watch in watchlist:
        if os.path.isfile(watch):
            checkFile(watch)
        elif os.path.isdir(watch):
            checkDir(watch)

    with open('watch-list.json', 'w') as o_watchlist_json:
        json.dump(watchlist, o_watchlist_json, sort_keys=True, indent=4)

if __name__ == "__main__":
    if platform.system() != 'Windows':
        watchListLoop()