import os
import threading
import time
import imgui
from array import array
from modules import logger

log = logger.Logger()
class NetWatch():

    name = ""
    description = ""

    watchLoopTime = 5.0
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
        
        rx_rate = self.bytesto(self.transmissionrate(self.adapters[self.curAdapter], "rx", 0.5), 'm')
        self.rx_bytes.append(rx_rate)

        if (len(self.rx_bytes) > 151):
            self.rx_bytes.pop(0)

        tx_rate = self.bytesto(self.transmissionrate(self.adapters[self.curAdapter], "tx", 0.5), 'm')
        self.tx_bytes.append(tx_rate)

        if (len(self.tx_bytes) > 151):
            self.tx_bytes.pop(0)

    def displayInterface(self):
        imgui.begin_child("left_bottom", width=606, height=370)
        imgui.text("Network Traffic")
        imgui.separator()
        imgui.spacing()

        plot_rx = array('f')
        for byte in self.rx_bytes:
            plot_rx.append(byte)

        plot_tx = array('f')
        for byte in self.tx_bytes:
            plot_tx.append(byte)

        imgui.text("Rx Traffic (MB) | AVG: " + str(sum(self.rx_bytes)/len(self.rx_bytes)))
        imgui.plot_lines("##Rx Traffic (MB)", plot_rx, graph_size=(606, 150))
        imgui.text("Tx Traffic (MB) | AVG: " + str(sum(self.tx_bytes)/len(self.tx_bytes)))
        imgui.plot_lines("##Tx Traffic (MB)", plot_tx, graph_size=(606, 150))
        imgui.end_child()

    def configurationInterface(self):
        changed, current = imgui.combo("Network Adapter", self.curAdapter, self.adapters)

        if changed:
            self.curAdapter = current
            self.rx_bytes = []
            self.rx_bytes.append(0)
            self.tx_bytes = []
            self.tx_bytes.append(0)

    def start(self):
        log.logNorm(self.name + " watch loop started...")

        self.adapters = os.listdir('/sys/class/net')

        self.started = True
        self.watchLoop()

    def stop(self):
        log.logAlert(self.name + " watch loop stopped.")
        self.started = False
        self.watchThread._delete()