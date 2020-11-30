import os
import platform
from datetime import *
import imgui
import threading
import json
import subprocess
import re
from modules import logger
from modules import LTKSModule

log = logger.Logger()
class SSHWatch(LTKSModule.LTKSModule):

    alerts = []

    watchLoopTime = 1.0
    started = False
    interfaceActive = False

    sshSelected = 0
    sshSelectionOptions = []
    activeConnections = {}

    banList = {}

    def __init__(self):
        with open('saves/ban-list.json') as banlist_json:
           self.banList = json.load(banlist_json)

        super().__init__("SSH Watcher", "This module is watches for SSH connects/disconnections along with allowing the user to quit a specific user SSH session.")

    def alert(self, message):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        self.alerts.append(timestampStr + " " + message)
        log.logAlert(message)

    def saveBanList(self):
        with open('saves/ban-list.json', 'w') as banlist_json:
            json.dump(self.banList, banlist_json, sort_keys=True, indent=4)

    def disconnectSSHConnection(self, conn):
        del self.sshSelectionOptions[self.sshSelected]
        subprocess.run("sudo pkill -9 -t " + conn, shell=True)
        del self.activeConnections[conn]

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()

        who = subprocess.check_output("who -uH", shell=True)
        cmdLines = who.decode().rstrip().split("\n")

        for line in cmdLines:
            lineInfo = line.split()
            if (lineInfo[1] not in self.activeConnections):
                if (lineInfo[1][0:-2] == "pts"):
                    con_time = datetime.strptime(lineInfo[2] + " " + lineInfo[3], '%Y-%m-%d %H:%M')

                    data = {
                        "ip": lineInfo[6][1:-1],
                        "ssh_proc": lineInfo[1],
                        "user": lineInfo[0],
                        "connected_time": con_time
                    }

                    if (data["user"] in self.banList["users"]):
                        self.alert("SSH User BANNED Connection Detected " + data["user"] + " (" + data["ip"] + ")")
                        subprocess.run("sudo pkill -9 -t " + data["ssh_proc"], shell=True)
                    else: 
                        self.activeConnections[lineInfo[1]] = data
                        self.alert("New SSH Connection Detected From " + data["user"] + " (" + data["ip"] + ")")
            
        for conn in list(self.activeConnections.keys()):
            if (not re.search(conn, who.decode())):
                del self.activeConnections[conn]

        self.sshSelectionOptions = []

        for conn in self.activeConnections:
            self.sshSelectionOptions.append("(" + self.activeConnections[conn]["ssh_proc"] + ") " + self.activeConnections[conn]["user"] + " " + self.activeConnections[conn]["ip"])


    def displayInterface(self):

        imgui.begin_child("left_bottom", width=606, height=370)


        imgui.text("SSH Connections")
        imgui.begin_child("left_bottom", width=606, height=310, border=True)

        imgui.begin_child("connections", width=606)

        imgui.columns(4, 'ssh_connections')
        imgui.text("ID")
        imgui.next_column()
        imgui.text("USER")
        imgui.next_column()
        imgui.text("IP")
        imgui.next_column()
        imgui.text("Time Connected")
        imgui.separator()

        imgui.set_column_width(0, 70)

        for conn in list(self.activeConnections.keys()):
            now = datetime.now()
            elapsed = now - self.activeConnections[conn]["connected_time"]
            imgui.next_column()
            imgui.text(self.activeConnections[conn]["ssh_proc"])
            imgui.next_column()
            imgui.text(self.activeConnections[conn]["user"])
            imgui.next_column()
            imgui.text(self.activeConnections[conn]["ip"]) 
            imgui.next_column()
            imgui.text(str(elapsed))

        imgui.columns(1)

        imgui.end_child()
        imgui.end_child()

        imgui.text("Select a SSH Session")

        clicked, current = imgui.combo(
            "##Path input", self.sshSelected, self.sshSelectionOptions
        )

        if (clicked):
            self.sshSelected = current

        imgui.same_line()

        if (imgui.button("Kick")):
            ssh_proc = self.sshSelectionOptions[self.sshSelected].split()[0][1:-1]
            log.logNorm("Kicked SSH Session (" + ssh_proc + ") " + self.activeConnections[ssh_proc]["user"])
            self.disconnectSSHConnection(ssh_proc)

        imgui.same_line()
        if (imgui.button("Ban User")):
            ssh_proc = self.sshSelectionOptions[self.sshSelected].split()[0][1:-1]
            username = self.sshSelectionOptions[self.sshSelected].split()[1]
            self.banList["users"].append(username)
            self.saveBanList()
            self.disconnectSSHConnection(ssh_proc)

        imgui.same_line()
        if (imgui.button("Ban IP")):
            pass
            

        imgui.end_child()


        imgui.same_line()

        imgui.begin_child("ssh_alerts")
        imgui.text("SSH Connections Alerts")

        imgui.begin_child("ssh_alerts_logger", border=True)

        for message in self.alerts:
            imgui.text_wrapped(message)

        imgui.end_child()
        imgui.end_child()

    def start(self):
        log.logNorm(self.name + " watch loop started...")
        self.started = True
        self.watchLoop()
