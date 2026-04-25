import multiprocessing
import os
import signal
import sqlite3
import sys
import threading
import warnings
from typing import Any

from Dmx import ManageDmxData
from Dmx.DBHandler import DBHandler

REC_NAME = "rec"
PLAY_NAME = "play"
SCENE_NONE = 0

START_REC = "start"
STOP_REC = "stop"
STOP_PLAY = "stop"
POISONING = "poisonPill"

"""
This is the Interface for all the DMX Recording/Playback, this is thread-save
"""
pipeToRec: multiprocessing.connection.Connection
pipeToPlay: multiprocessing.connection.Connection
pipeToRecLock = threading.Lock()
pipeToPlayLock = threading.Lock()


def shutdownHandler(signum, frame):
    # we probably overite the flask SIGINT handler so we have to call sys.exit to shut down flaks
    print("-------- shutting down --------")
    sendIntoPipeRec((POISONING,))
    sendIntoPipePlay(POISONING)
    sys.exit(0)


def startBackgroundProcesses(dbPath: str):
    signal.signal(signal.SIGINT, shutdownHandler)

    # check if db file exists
    if not os.path.exists(dbPath):
        warnings.warn(message='DB not existing. Pleas run db init command. Disabling Dmx Playback/Recording', category=Warning)
        return
    global pipeToRec, pipeToPlay
    pipeToRec, pipeToPlay = ManageDmxData.startAsProcess(dbPath)


def sendIntoPipeRec(obj: Any):
    global pipeToRecLock
    with pipeToRecLock:
        global pipeToRec
        pipeToRec.send(obj)


def sendIntoPipePlay(obj: Any):
    global pipeToPlayLock
    with pipeToPlayLock:
        global pipeToPlay
        pipeToPlay.send(obj)


def startRecordingNewScene(sceneName, static: bool = False):
    sendIntoPipeRec((START_REC, sceneName, static))


def stopRecordingNewScene():
    sendIntoPipeRec((STOP_REC,))


def deleteScene(db: sqlite3.Connection, sceneId: int):
    DBHandler(db).deleteScene(sceneId)


def startPlayer(sceneId: int):
    sendIntoPipePlay(sceneId)


def stopPlayer():
    sendIntoPipePlay(STOP_PLAY)


def getCurrantRecording(db: sqlite3.Connection, ) -> str:
    return "TODO"


def getCurrantScenes(db: sqlite3.Connection, ) -> list[tuple[int, int]]:
    return DBHandler(db).getCurrantScenes()
