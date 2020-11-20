import os
import platform
from datetime import *
import imgui
import threading
import json
from modules import logger
from modules import LTKSModule

log = logger.Logger()
class SSHWatch(LTKSModule.LTKSModule):

    alerts = []

    watchLoopTime = 30.0
    started = False
    interfaceActive = False

    activeConnections = {}

    addingPathText = ""

    def __init__(self):
        super().__init__("SSH Watcher", "This module is watches for SSH connects/disconnections along with allowing the user to quit a specific user SSH session.")

    def alert(self, message, data):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        self.alerts.append(timestampStr + " ALERT | " + message)
        log.logAlert(message)

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()

        authFile = open("/var/log/auth.log")

        for line in authFile.readlines():
            if "sshd" in line:
                lineList = line.split(" ")
                if ("Accepted" in line):
                    data = {
                        "ip": lineList[10],
                        "port": lineList[12],
                        "ssh_proc": lineList[4],
                        "user": lineList[8]
                    }
                    self.activeConnections[lineList[12]] = data

                if ("Disconnected" in line):
                    # 8,9,11
                    lineList[11] = lineList[11].strip('\n')
                    if (lineList[11] in self.activeConnections):
                        del self.activeConnections[lineList[11]]

    def displayInterface(self):
        imgui.begin_child("left_bottom", width=606, height=370)

        for conn in self.activeConnections:
            imgui.text(self.activeConnections[conn]["port"])


        imgui.end_child()

    def start(self):
        log.logNorm(self.name + " watch loop started...")
        self.started = True
        self.watchLoop()
