import os
import platform
import datetime
import threading
import json
from modules import logger

log = logger.Logger()
class FileWatch():

    name = ""
    description = ""

    watchLoopTime = 30.0
    started = False

    def __init__(self):
        self.name = "File/Directory Watcher"
        self.description = "This module is responsible for timely checks on certain directories and files to see if anything has changed"


        log.logNorm(self.name + " initiated.")
        with open('watch-list.json') as placesToWatch_json:
           self.placesToWatch = json.load(placesToWatch_json)

    def checkFile(self, path):
        fileStat = os.stat(path)
        if not path in self.placesToWatch:
            self.placesToWatch[path]["last-modified"] = fileStat.st_mtime

        if float(self.placesToWatch[path]["last-modified"]) >= fileStat.st_mtime:
            with open(path) as watch_file:
                self.placesToWatch[path]["last-content"] = watch_file.read()
        else:
            with open(path) as watch_file:
                log.logAlert("A file (" + path + ") has been modified!")

            self.placesToWatch[path]["last-modified"] = fileStat.st_mtime

    def checkDir(self, path):
        dirStat = os.stat(path)
        if self.placesToWatch[path]["last-modified"] == "None":
            self.placesToWatch[path]["last-modified"] = dirStat.st_mtime

        if float(self.placesToWatch[path]["last-modified"]) >= dirStat.st_mtime:
            self.placesToWatch[path]["last-content"] = ""
            for file in os.listdir(path):
                if os.path.isfile(file):
                    self.placesToWatch[path]["last-content"] += "   \u001b[0m- " + file + "\n"
                elif os.path.isdir(file):
                    self.placesToWatch[path]["last-content"] += "   \u001b[0m- \u001b[36m" + file + "\n"
        else:
            files = ""
            for file in os.listdir(path):
                if os.path.isfile(file):
                    files += "   \u001b[0m- " + file + "\n"
                elif os.path.isdir(file):
                    files += "   \u001b[0m- \u001b[36m" + file + "\n"


            log.logAlert("A directory (" + path +") has been modified.")
            self.placesToWatch[path]["last-modified"] = dirStat.st_mtime

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()
        for watch in self.placesToWatch:
            if os.path.isfile(watch):
                self.checkFile(watch)
            elif os.path.isdir(watch):
                self.checkDir(watch)

        with open('watch-list.json', 'w') as placesToWatch_json:
            json.dump(self.placesToWatch, placesToWatch_json, sort_keys=True, indent=4)

    def start(self):
        log.logNorm("File and directory watch loop started...")
        self.started = True
        self.watchLoop()

    def stop(self):
        log.logAlert("File and directory watch loop stopped.")
        self.started = False
        self.watchThread._delete()