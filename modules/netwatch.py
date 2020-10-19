import os
import platform
import datetime
import threading
import json
import time
from modules import logger

log = logger.Logger()
class NetWatch():

    name = ""
    description = ""

    watchLoopTime = 3.0
    started = False

    rx_bytes = []
    tx_bytes = []

    curAdapter = "enp9s0"

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
        """Return the transmisson rate of a interface under linux
        dev: devicename
        direction: rx (received) or tx (sended)
        timestep: time to measure in seconds
        """
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
        
        rate = self.bytesto(self.transmissionrate(self.curAdapter, "rx", 2), 'k')

        log.logNorm(str(rate))

    def start(self):
        log.logNorm(self.name + " watch loop started...")
        self.started = True
        self.watchLoop()

    def stop(self):
        log.logNorm(self.name + " watch loop stopped.")
        self.started = False
        self.watchThread._delete()