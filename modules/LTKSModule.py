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

    def watchLoop(self):
        pass

    def displayInterface(self):
        pass

    def configurationInterface(self):
       pass

    def start(self):
        log.logNorm(self.name + " watch loop started...")

        self.started = True
        self.watchLoop()

    def stop(self):
        log.logAlert(self.name + " watch loop stopped.")
        self.started = False
        self.watchThread._delete()