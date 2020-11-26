import os
import threading
import time
from datetime import datetime
import imgui
import numpy
from array import array
from modules import logger
from modules import LTKSModule

log = logger.Logger()
class NetWatch(LTKSModule.LTKSModule):
    triggerPercent = 20
    alertFloor = 0.5

    watchLoopTime = 5.0
    started = False
    interfaceActive = False
    alerts = []

    rx_bytes = []
    tx_bytes = []

    adapters = []
    curAdapter = 0

    def __init__(self):
        super().__init__("Network Traffic Monitor", "This module is responsible for timely checks on network data usage")

    def bytesto(self, bytes, to, bsize=1024):
        a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
        r = float(bytes)
        for i in range(a[to]):
            r = r / bsize

        return(r)

    def alert(self, message):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        self.alerts.append(timestampStr + " " + message)
        log.logAlert(message)

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

    def rxByteHandling(self):
        rx_rate = self.bytesto(self.transmissionrate(self.adapters[self.curAdapter], "rx", 0.5), 'm')
        self.rx_bytes.append(rx_rate)

        if (len(self.rx_bytes) > 151):
            self.rx_bytes.pop(0)

        if (len(self.tx_bytes) >= 150):
            if (rx_rate >= self.alertFloor):
                rx_avg = round(sum(self.rx_bytes)/len(self.rx_bytes), 5)
                rx_trigger = rx_avg * (self.triggerPercent/100)

                if self.rx_bytes[len(self.rx_bytes) - 1] >= rx_avg + rx_trigger:
                    if self.rx_bytes[len(self.rx_bytes) - 1] > self.rx_bytes[len(self.rx_bytes) - 2]:
                        self.alert("Download Traffic Rate Peaked at: " + str(round(rx_rate, 5)))

    def txByteHandling(self):
        tx_rate = self.bytesto(self.transmissionrate(self.adapters[self.curAdapter], "tx", 0.5), 'm')
        self.tx_bytes.append(tx_rate)

        if (len(self.tx_bytes) > 151):
            self.tx_bytes.pop(0)

        if (len(self.tx_bytes) >= 150):
            if (tx_rate >= self.alertFloor):
                tx_avg = round(sum(self.tx_bytes)/len(self.tx_bytes), 5)
                tx_trigger = tx_avg * (self.triggerPercent/100)

                if self.tx_bytes[len(self.tx_bytes) - 1] >= tx_avg + tx_trigger:
                    if self.tx_bytes[len(self.tx_bytes) - 1] > self.tx_bytes[len(self.tx_bytes) - 2]:
                        self.alert("Upload Traffic Rate Peaked at: " + str(round(tx_rate, 5)))

    def watchLoop(self):
        self.watchThread = threading.Timer(self.watchLoopTime, self.watchLoop)
        self.watchThread.setDaemon(True)
        self.watchThread.start()

        self.rxByteHandling()
        self.txByteHandling()

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

        imgui.text("Download Traffic (MB) | Avg: " + str(round(sum(self.rx_bytes)/len(self.rx_bytes), 5)) + " mb | Max: " + str(round(max(self.rx_bytes), 5)) + " mb")
        imgui.plot_lines("##Rx Traffic (MB)", plot_rx, graph_size=(606, 150))
        imgui.spacing()
        imgui.text("Upload Traffic (MB) | Avg: " + str(round(sum(self.tx_bytes)/len(self.tx_bytes), 5)) + " mb | Max: " + str(round(max(self.tx_bytes), 5)) + " mb")
        imgui.plot_lines("##Tx Traffic (MB)", plot_tx, graph_size=(606, 150))
        imgui.end_child()

        imgui.same_line()

        imgui.begin_child("net_traf_alerts")
        imgui.text("Network Traffic Alerts")

        imgui.begin_child("net_traf_alerts_logger", border=True)

        for message in self.alerts:
            imgui.text_wrapped(message)

        imgui.end_child()
        imgui.end_child()

    def configurationInterface(self):
        super().configurationInterface()

        changed, current = imgui.combo("Network Adapter", self.curAdapter, self.adapters)

        if changed:
            self.curAdapter = current
            self.rx_bytes = []
            self.rx_bytes.append(0)
            self.tx_bytes = []
            self.tx_bytes.append(0)
            log.logNorm("Network watch interface changed: " + self.adapters[current])

        percent_changed, percent_val = imgui.input_int("Trigger Percent", self.triggerPercent, 5)

        if percent_changed:
            self.triggerPercent = percent_val

        floor_changed, floor_val = imgui.input_float("Alert Floor", self.alertFloor, 0.005)

        if floor_changed:
            self.alertFloor = floor_val

    def start(self):
        log.logNorm(self.name + " watch loop started...")

        self.adapters = os.listdir('/sys/class/net')

        self.started = True
        self.watchLoop()
