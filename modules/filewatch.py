import os
import platform
from datetime import *
import imgui
import threading
import json
from modules import logger

log = logger.Logger()
class FileWatch():

    name = ""
    description = ""

    alerts = []

    watchLoopTime = 30.0
    started = False
    interfaceActive = False

    addingPathText = ""

    def __init__(self):
        self.name = "File/Directory Watcher"
        self.description = "This module is responsible for timely checks on certain directories and files to see if anything has changed"


        log.logNorm(self.name + " initiated.")
        with open('watch-list.json') as watchInformation_json:
           self.watchInformation = json.load(watchInformation_json)

    def alert(self, message):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        self.alerts.append(timestampStr + " ALERT | " + message)
        log.logAlert(message)

    def checkFile(self, path):
        fileStat = os.stat(path)
        if self.watchInformation[path]["last-modified"] == "None":
            self.watchInformation[path]["last-modified"] = fileStat.st_mtime

        if float(self.watchInformation[path]["last-modified"]) >= fileStat.st_mtime:
            with open(path) as watch_file:
                self.watchInformation[path]["last-content"] = watch_file.read()
        else:
            with open(path) as watch_file:
                log.logAlert("A file (" + path + ") has been modified!")

            self.watchInformation[path]["last-modified"] = fileStat.st_mtime

    def checkDir(self, path):
        dirStat = os.stat(path)
        if self.watchInformation[path]["last-modified"] == "None":
            self.watchInformation[path]["last-modified"] = dirStat.st_mtime

        if float(self.watchInformation[path]["last-modified"]) >= dirStat.st_mtime:
            self.watchInformation[path]["last-content"] = ""
            for file in os.listdir(path):
                if os.path.isfile(file):
                    self.watchInformation[path]["last-content"] += "   \u001b[0m- " + file + "\n"
                elif os.path.isdir(file):
                    self.watchInformation[path]["last-content"] += "   \u001b[0m- \u001b[36m" + file + "\n"
        else:
            files = ""
            for file in os.listdir(path):
                if os.path.isfile(file):
                    files += "   \u001b[0m- " + file + "\n"
                elif os.path.isdir(file):
                    files += "   \u001b[0m- \u001b[36m" + file + "\n"


            log.logAlert("A directory (" + path +") has been modified.")
            self.watchInformation[path]["last-modified"] = dirStat.st_mtime

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()
        for watch in self.watchInformation:
            if os.path.isfile(watch):
                self.checkFile(watch)
            elif os.path.isdir(watch):
                self.checkDir(watch)

        with open('watch-list.json', 'w') as watchInformation_json:
            json.dump(self.watchInformation, watchInformation_json, sort_keys=True, indent=4)

    def configurationInterface(self):
        pass

    def displayInterface(self):
        imgui.begin_child("left_bottom", width=606, height=370)


        imgui.text("Watch Paths")
        imgui.begin_child("left_bottom", width=606, height=310, border=True)

        for path in list(self.watchInformation.keys()):
            imgui.text(path)
            imgui.same_line()
            if (imgui.button("- Remove Path")):
                del self.watchInformation[path]
                with open('watch-list.json', 'w') as watchInformation_json:
                    json.dump(self.watchInformation, watchInformation_json, sort_keys=True, indent=4)
        imgui.end_child()

        imgui.text("Add new path:")

        addNewPathInputChanged, self.addingPathText = imgui.input_text(
            "##Path input",
            self.addingPathText,
            2048
        )

        imgui.same_line()

        if (imgui.button("+ Add Path")):
            newPath = {
                'last-modified': "None",
                'last-content': ''
            }

            self.watchInformation[self.addingPathText] = newPath
            with open('watch-list.json', 'w') as watchInformation_json:
                json.dump(self.watchInformation, watchInformation_json, sort_keys=True, indent=4)

        imgui.end_child()

        imgui.same_line()

        imgui.begin_child("file_dir_alerts")
        imgui.text("File/Directory Change Alerts")

        imgui.begin_child("file_dir_alerts_logger", border=True)

        for message in self.alerts:
            imgui.text_wrapped(message)

        imgui.end_child()
        imgui.end_child()

    def start(self):
        log.logNorm("File and directory watch loop started...")
        self.started = True
        self.watchLoop()

    def stop(self):
        log.logAlert("File and directory watch loop stopped.")
        self.started = False
        self.watchThread._delete()