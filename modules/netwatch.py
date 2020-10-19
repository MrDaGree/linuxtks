import os
import platform
import datetime
import threading
import json
import time
import imgui
from modules import logger

log = logger.Logger()
class NetWatch():

    name = ""
    description = ""

    watchLoopTime = 3.0
    started = False

    rx_bytes = []
    tx_bytes = []

    adapters = []
    curAdapter = 0

    def __init__(self):
        self.name = "Network Traffic Monitor"
        self.description = "This module is responsible for timely checks on network data usage"


        log.logNorm(self.name + " initiated.")

    def bytesto(self, bytes, to, bsize=1024):
        a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
        r = float(bytes)
        for i in range(a[to]):
            r = r / bsize

        return(r)

    def transmissionrate(self, dev, direction, timestep):
        path = "/sys/class/net/{}/statistics/{}_bytes".format(dev, direction)
        f = open(path, "r")
        bytes_before = int(f.read())
        f.close()
        time.sleep(timestep)
        f = open(path, "r")
        bytes_after = int(f.read())
        f.close()
        return (bytes_after-bytes_before)/timestep

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()
        
        rate = self.bytesto(self.transmissionrate(self.adapters[self.curAdapter], "rx", 2), 'k')

        log.logNorm(str(rate))

    def configurationInterface(self):
        changed, current = imgui.combo("Network Adapter", self.curAdapter, self.adapters)

        if changed:
            self.curAdapter = current

    def start(self):
        log.logNorm(self.name + " watch loop started...")

        self.adapters = os.listdir('/sys/class/net')

        self.started = True
        self.watchLoop()

    def stop(self):
        log.logAlert(self.name + " watch loop stopped.")
        self.started = False
        self.watchThread._delete()