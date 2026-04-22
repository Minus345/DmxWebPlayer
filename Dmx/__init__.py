import os
import signal
import sqlite3

from Dmx import ManageDmxData
from Dmx.DBHandler import DBHandler

REC_NAME = "rec"
PLAY_NAME = "play"
SCENE_NONE = 0

"""
This is the Interface for all the DMX Recording/Playback
"""

def startBackgroundProcesses(dbPath: str):
    # TODO check if db file exists
    # TODO make init db command work -> delay startup Processes
    ManageDmxData.startAsProcess(dbPath)


class _Base:
    def __init__(self, db: sqlite3.Connection):
        self.dbHandler = DBHandler(db)


class Editor(_Base):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db)
        self.pidReceiverProcess = self.dbHandler.getPidFromProcess(REC_NAME)

    def startRecordingNewScene(self, sceneId):
        self.dbHandler.updateUtilDbSceneName(REC_NAME, sceneId)
        os.kill(self.pidReceiverProcess, signal.SIGUSR1)

    def stopRecordingNewScene(self):
        os.kill(self.pidReceiverProcess, signal.SIGUSR2)

    def deleteScene(self, sceneId: int):
        self.dbHandler.deleteScene(sceneId)


class Player(_Base):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db)

    def startPlayer(self, sceneId: int):
        self.dbHandler.updateUtilDbSceneName(PLAY_NAME, sceneId)
        self.__activateStart()

    def stopPlayer(self):
        self.dbHandler.updateUtilDbSceneName(PLAY_NAME, SCENE_NONE)
        self.__activateStart()

    def __activateStart(self):
        pidReceiverProcess = self.dbHandler.getPidFromProcess(PLAY_NAME)
        os.kill(pidReceiverProcess, signal.SIGUSR1)


class Viewer(_Base):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db)

    def getCurrantRecording(self) -> str:
        return self.dbHandler.getCurrantUtilName(REC_NAME)

    def getCurrantScenes(self) -> list[tuple[int, int]]:
        return self.dbHandler.getCurrantScenes()
