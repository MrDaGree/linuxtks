import os
import time
import imgui
import threading
import numpy
import json
from datetime import *
from array import array
from modules import logger


log = logger.Logger()
class LTKSModule():
    name = ""
    description = ""
    started = False

    def __init__(self, name, description):
        self.name = name
        self.description = description


        log.logNorm(self.name + " initiated.")
        self.start()

    def watchLoop(self):
        pass

    def displayInterface(self):
        pass

    def configurationInterface(self):
        imgui.text_wrapped(self.description)

        imgui.spacing()

        if not self.started:
            if imgui.button("Start"):
                self.start()
        else:
            if imgui.button("Stop"):
                self.stop()

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

    def start(self):
        log.logNorm(self.name + " watch loop started...")

        self.started = True
        self.watchLoop()

    def stop(self):
        log.logAlert(self.name + " watch loop stopped.")
        self.started = False
        self.watchThread._delete()