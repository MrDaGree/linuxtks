from datetime import datetime

class Logger:

    log = []

    def __init__(self):
        pass

    def logNorm(self, message):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        print("LTKS: " + message)
        self.log.append(timestampStr + " LOG | " + message)

    def logError(self, message):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        print("LTKS [ERROR]: " + message)
        self.log.append(timestampStr + " ERROR | " + message)

    def logAlert(self, message):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("[%m-%d-%Y] [%H:%M:%S]")

        print("LTKS [ALERT]: " + message)
        self.log.append(timestampStr + " ALERT | " + message)

    def getLogs(self):
        return self.log