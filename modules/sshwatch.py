import os
import platform
from datetime import *
import imgui
import threading
import json
import subprocess
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

        print(subprocess.check_output("who -uH", shell=True))

        authFile = open("/var/log/auth.log")

        for line in authFile.readlines():
            if "sshd" in line:
                lineList = line.split(" ")
                if ("Accepted" in line):
                    now = datetime.now()
                    con_time = datetime.strptime(lineList[0] + " " + lineList[1] + " " + str(now.year) + " " + lineList[2], '%b %d %Y %H:%M:%S')
                    data = {
                        "ip": lineList[10],
                        "port": lineList[12],
                        "ssh_proc": lineList[4],
                        "user": lineList[8],
                        "connected_time": con_time
                    }
                    self.activeConnections[lineList[12]] = data

                if ("Disconnected" in line):
                    # 8,9,11
                    lineList[11] = lineList[11].strip('\n')
                    if (lineList[11] in self.activeConnections):
                        del self.activeConnections[lineList[11]]

    def displayInterface(self):

        imgui.begin_child("left_bottom", width=606, height=370)


        imgui.text("SSH Connections")
        imgui.begin_child("left_bottom", width=606, height=352, border=True)

        imgui.begin_child("connections", width=606)

        for conn in self.activeConnections:
            now = datetime.now()
            elapsed = now - self.activeConnections[conn]["connected_time"]
            imgui.text(self.activeConnections[conn]["ip"] + ":" + self.activeConnections[conn]["port"] + " (" + self.activeConnections[conn]["user"] + ") " + self.activeConnections[conn]["ssh_proc"] + " | Elapsed Time: " + str(elapsed))
            imgui.same_line()
            if (imgui.button("Kick")):
                pass

        imgui.end_child()
        imgui.end_child()
        imgui.end_child()


        imgui.same_line()

        imgui.begin_child("ssh_alerts")
        imgui.text("SSH Connections Alerts")

        imgui.begin_child("ssh_alerts_logger", border=True)

        imgui.end_child()
        imgui.end_child()

    def start(self):
        log.logNorm(self.name + " watch loop started...")
        self.started = True
        self.watchLoop()
