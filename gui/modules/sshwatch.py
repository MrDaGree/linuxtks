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
    activeInterface = "main"

    sshSelected = 0
    sshSelectionOptions = []
    activeConnections = {}

    banList = {}
    banUserSelected = 0
    banIPSelected = 0

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

    def handleDisconnectingCurrentSelection(self):
        ssh_proc = self.sshSelectionOptions[self.sshSelected].split()[0][1:-1]
        self.disconnectSSHConnection(ssh_proc)

    def handleBanningUser(self):
        ssh_proc = self.sshSelectionOptions[self.sshSelected].split()[0][1:-1]
        username = self.sshSelectionOptions[self.sshSelected].split()[1]
        self.alert("Banning user (" + username + ") on SSH Process " + ssh_proc)
        self.banList["users"].append(username)
        self.saveBanList()

    def handleBanningIPAddr(self):
        ssh_proc = self.sshSelectionOptions[self.sshSelected].split()[0][1:-1]
        ip_addr = self.sshSelectionOptions[self.sshSelected].split()[2]
        self.alert("Banning IP (" + ip_addr + ") on SSH Process " + ssh_proc)
        self.banList["ip_addresses"].append(ip_addr)
        self.saveBanList()

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
                        self.alert("SSH User BANNED Connection Detected from " + data["user"] + " (" + data["ip"] + ")")
                        subprocess.run("sudo pkill -9 -t " + data["ssh_proc"], shell=True)
                    elif (data["ip"] in self.banList["ip_addresses"]):
                        self.alert("SSH IP BANNED Connection Detected from " + data["user"] + " (" + data["ip"] + ")")
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


    def moduleMenuBar(self, modules):
        if (imgui.begin_menu(self.name)):

            main_c, _ = imgui.menu_item("Main Interface")
            if main_c:
                for _, moduleToDisable in modules.items():
                    moduleToDisable.interfaceActive = False
                self.interfaceActive = not self.interfaceActive
                self.activeInterface = "main"

            banList_c, _ = imgui.menu_item("Ban List")
            if banList_c:
                for _, moduleToDisable in modules.items():
                    moduleToDisable.interfaceActive = False
                self.interfaceActive = not self.interfaceActive
                self.activeInterface = "ban"

            imgui.end_menu()
                

    def displayInterface(self):

        imgui.begin_child("left_bottom", width=606, height=370)



        if (self.activeInterface == "main"):

            imgui.text("Main Interface (SSH)")
            imgui.begin_child("left_bottom", width=606, height=290, border=True)

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

            if (imgui.button("Kick")):
                ssh_proc = self.sshSelectionOptions[self.sshSelected].split()[0][1:-1]
                log.logNorm("Kicked SSH Session (" + ssh_proc + ") " + self.activeConnections[ssh_proc]["user"])
                self.disconnectSSHConnection(ssh_proc)

            imgui.same_line()
            if (imgui.button("Ban Both")):
                self.handleBanningUser()
                self.handleBanningIPAddr()
                self.handleDisconnectingCurrentSelection()

            imgui.same_line()
            if (imgui.button("Ban User")):
                self.handleBanningUser()
                self.handleDisconnectingCurrentSelection()

            imgui.same_line()
            if (imgui.button("Ban IP")):
                self.handleBanningIPAddr()
                self.handleDisconnectingCurrentSelection()
                

        elif (self.activeInterface == "ban"):
            imgui.text("Ban List (SSH)")
            imgui.begin_child("left_bottom", width=299, height=310, border=True)

            imgui.columns(2, 'ssh_connections')
            imgui.text("USERNAME")
            imgui.next_column()
            imgui.next_column()
            imgui.separator()

            for user in self.banList["users"]:
                imgui.text(user)
                imgui.next_column()

            imgui.columns(1)
            imgui.end_child()

            imgui.same_line()

            imgui.begin_child("right_bottom", width=299, height=310, border=True)
            imgui.text("IP Address")
            imgui.next_column()
            imgui.next_column()
            imgui.separator()

            for user in self.banList["ip_addresses"]:
                imgui.text(user)
                imgui.next_column()

            imgui.columns(1)
            imgui.end_child()

            imgui.begin_child("left_selection", width=299)

            clicked, current = imgui.combo(
                "##Path input", self.banUserSelected, self.banList["users"]
            )

            imgui.same_line()

            if (imgui.button("Unban")):
                self.alert("Unbanning User (" + self.banList["users"][self.banUserSelected] + ")")
                del self.banList["users"][self.banUserSelected]
                self.saveBanList()

            imgui.end_child()

            imgui.same_line()

            imgui.begin_child("right_selection", width=299)

            clicked, current = imgui.combo(
                "##Path input", self.banIPSelected, self.banList["ip_addresses"]
            )

            imgui.same_line()

            if (imgui.button("Unban")):
                self.alert("Unbanning IP (" + self.banList["ip_addresses"][self.banIPSelected] + ")")
                del self.banList["ip_addresses"][self.banIPSelected]
                self.saveBanList()

            imgui.end_child()


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
