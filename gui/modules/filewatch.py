import os
import platform
from datetime import *
import imgui
import threading
import json
from modules import logger
from modules import LTKSModule

log = logger.Logger()
class FileWatch(LTKSModule.LTKSModule):

    alerts = []
    alertsData = {}

    watchLoopTime = 30.0
    started = False
    interfaceActive = False

    addingPathText = ""

    def __init__(self):
        with open('saves/watch-list.json') as watchInformation_json:
           self.watchInformation = json.load(watchInformation_json)

        super().__init__("File/Directory Watcher", "This module is responsible for timely checks on certain directories and files to see if anything has changed")

    def alert(self, message, data):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        data["timestamp"] = timestampStr

        self.alertsData[len(self.alertsData) + 1] = data

        self.alerts.append(timestampStr + " " + message)
        log.logAlert(message)

    def saveWatchInformation(self):
        with open('saves/watch-list.json', 'w') as watchInformation_json:
            json.dump(self.watchInformation, watchInformation_json, sort_keys=True, indent=4)

    def handleFileAlert(self, path):
        with open(path) as watch_file:
            content = watch_file.read()
            data = {}
            data["path"] = path
            data["last-content"] = self.watchInformation[path]["last-content"]
            data["new-content"] = content

            self.alert("A file (" + path + ") has been modified!", data)
            self.watchInformation[path]["last-content"] = content



    def checkFile(self, path):
        fileStat = os.stat(path)

        if float(self.watchInformation[path]["last-modified"]) < fileStat.st_mtime:
            self.handleFileAlert(path)

            self.watchInformation[path]["last-modified"] = fileStat.st_mtime
            self.saveWatchInformation()

    def handleUpdatingDirInformation(self, path):
        self.watchInformation[path]["dir-content"] = {}
        self.watchInformation[path]["dir-content"]["files"] = []
        self.watchInformation[path]["dir-content"]["directories"] = []
        for file in os.listdir(path):
            if os.path.isfile(file):
                self.watchInformation[path]["dir-content"]["files"].append(file)
            elif os.path.isdir(file):
                self.watchInformation[path]["dir-content"]["directories"].append(file)

    def handleDirectoryAlert(self, path):
        data = {}
        data["path"] = path
        data["last-content"] = self.watchInformation[path]["dir-content"]
        data["new-content"] = {}
        data["new-content"]["directories"] = []
        data["new-content"]["files"] = []

        for file in os.listdir(path):
            if os.path.isfile(file):
                data["new-content"]["files"].append(file)
            elif os.path.isdir(file):
                data["new-content"]["directories"].append(file)

        self.alert("A directory (" + path + ") has been modified!", data)
        self.handleUpdatingDirInformation(path)

    def checkDir(self, path):
        dirStat = os.stat(path)

        if float(self.watchInformation[path]["last-modified"]) < dirStat.st_mtime:
            self.handleDirectoryAlert(path)
            self.watchInformation[path]["last-modified"] = dirStat.st_mtime
            self.saveWatchInformation()

            

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()
        for watch in self.watchInformation:
            if os.path.isfile(watch):
                self.checkFile(watch)
            elif os.path.isdir(watch):
                self.checkDir(watch)

        self.saveWatchInformation()

    def handleNewDirAdding(self):
        newPath["dir-content"] = {}
        newPath["dir-content"]["files"] = []
        newPath["dir-content"]["directories"] = []
        for file in os.listdir(self.addingPathText):
            print(file, os.path.isfile(file), os.path.isdir(file))
            if os.path.isfile(file):
                newPath["dir-content"]["files"].append(file)
            if os.path.isdir(file):
                newPath["dir-content"]["directories"].append(file)

    def handleNewPathAdding(self):
        if (os.path.isfile(self.addingPathText) or os.path.isdir(self.addingPathText)):
            dirStat = os.stat(self.addingPathText)

            newPath = {
                'last-modified': dirStat.st_mtime,
            }

            if (os.path.isfile(self.addingPathText)):
                with open(self.addingPathText) as watch_file:
                    newPath['last-content'] = watch_file.read()

            if (os.path.isdir(self.addingPathText)):
                self.handleNewDirAdding()

            self.watchInformation[self.addingPathText] = newPath
            self.saveWatchInformation()

    def displayInterface(self):
        imgui.begin_child("left_bottom", width=606, height=370)


        imgui.text("Watch Paths")
        imgui.begin_child("left_bottom", width=606, height=310, border=True)

        for path in list(self.watchInformation.keys()):
            imgui.push_text_wrap_position()
            imgui.text(path)
            imgui.same_line()
            if (imgui.button("- Remove Path")):
                del self.watchInformation[path]
                self.saveWatchInformation()

        imgui.end_child()

        imgui.text("Add new path:")

        addNewPathInputChanged, self.addingPathText = imgui.input_text(
            "##Path input",
            self.addingPathText,
            2048
        )

        imgui.same_line()

        if (imgui.button("+ Add Path")):
            self.handleNewPathAdding()

        imgui.end_child()

        imgui.same_line()

        imgui.begin_child("file_dir_alerts")
        imgui.text("File/Directory Change Alerts")

        imgui.begin_child("file_dir_alerts_logger", border=True)

        for alert in self.alertsData:
            data = self.alertsData[alert]
            if (imgui.tree_node(data["timestamp"] + " " + data["path"])):
                imgui.indent()
                imgui.push_text_wrap_position()
                imgui.text("Change Path: " + data["path"])
                if (os.path.isfile(data["path"])):
                    if (imgui.tree_node("Last Content")):
                        imgui.push_text_wrap_position()
                        imgui.text(data["last-content"])
                        imgui.tree_pop()
                    if (imgui.tree_node("New Content")):
                        imgui.push_text_wrap_position()
                        imgui.text(data["new-content"])
                        imgui.tree_pop()

                if (os.path.isdir(data["path"])):
                    if (imgui.tree_node("Last Content")):
                        if (imgui.tree_node("Files (" + str(len(data["last-content"]["files"])) + ")")):
                            for file in data["last-content"]["files"]:
                                imgui.push_text_wrap_position()
                                imgui.text(file)
                            imgui.tree_pop()
                        if (imgui.tree_node("Directories (" + str(len(data["last-content"]["directories"])) + ")")):
                            for file in data["last-content"]["directories"]:
                                imgui.push_text_wrap_position()
                                imgui.text(file)
                            imgui.tree_pop()
                        imgui.tree_pop()
                    if (imgui.tree_node("New Content")):
                        if (imgui.tree_node("Files (" + str(len(data["new-content"]["files"])) + ")")):
                            for file in data["new-content"]["files"]:
                                imgui.push_text_wrap_position()
                                imgui.text(file)
                            imgui.tree_pop()
                        if (imgui.tree_node("Directories (" + str(len(data["new-content"]["directories"])) + ")")):
                            for file in data["new-content"]["directories"]:
                                imgui.push_text_wrap_position()
                                imgui.text(file)
                            imgui.tree_pop()
                        imgui.tree_pop()

                imgui.tree_pop()
                imgui.unindent()

        imgui.end_child()
        imgui.end_child()

    def start(self):
        log.logNorm(self.name + " watch loop started...")
        self.started = True
        self.watchLoop()
