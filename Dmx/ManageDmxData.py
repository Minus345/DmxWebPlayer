import multiprocessing as mp
import os
import signal
import sqlite3
import time
from sqlite3 import Connection
from typing import override

import sacn

import Dmx
from Dmx.StoreDmxData import Scene, Frame


class BackgroundProcess:
    db: Connection
    curScene: Scene
    processName: str
    dataAction = False
    running = True

    def sigHandlerStart(self, signum, frame):
        self.dataAction = True

    def sigHandlerStop(self, signum, frame):
        self.dataAction = False

    def shutdownHandler(self, signum, frame):
        print("shutdown")
        self.running = False

    def loop(self, databasePath: str):
        pass

    def setup(self, databasePath: str):
        ## init db
        self.db = sqlite3.connect(
            databasePath,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.db.row_factory = sqlite3.Row

        cur = self.db.cursor()

        # check if db is initialized
        isInitialized = cur.execute("SELECT COUNT(*) FROM util WHERE name = ?", (self.processName,)).fetchone()[0]
        if isInitialized <= 0:
            raise Exception('DB not initialised')

        data = (os.getpid(), Dmx.SCENE_NONE, self.processName)
        cur.execute(
            "UPDATE util SET pid = ?, scene = ? WHERE name = ?", data)
        self.db.commit()

        signal.signal(signal.SIGUSR1, self.sigHandlerStart)
        signal.signal(signal.SIGUSR2, self.sigHandlerStop)
        signal.signal(signal.SIGTERM, self.shutdownHandler)
        signal.signal(signal.SIGINT, self.shutdownHandler)


class Recording(BackgroundProcess):
    def __init__(self):
        self.processName = Dmx.REC_NAME

    @override
    def loop(self, databasePath: str):
        super().setup(databasePath)
        while self.running:
            signal.pause()
            if self.dataAction:
                self.recordDmx()

    def recordDmx(self):
        ## get scene name from db or shutdown request
        cur = self.db.cursor()
        name = cur.execute("""SELECT scene
                              FROM util
                              WHERE name == ?""", (Dmx.REC_NAME,)).fetchone()['scene']

        if name == Dmx.SCENE_NONE:
            print("[REC] no scene name defined")
            self.dataAction = False
            return
        self.curScene = Scene(name)

        ## start recording
        print("[REC] start recording: " + name)

        receiver = sacn.sACNreceiver(bind_address='192.168.188.20')

        @receiver.listen_on('universe', universe=1)
        def callback(packet):  # packet type: sacn.DataPacket
            if packet.dmxStartCode == 0x00:  # ignore non-DMX-data packets
                curTime = time.time()
                print(packet.dmxData)

                if len(self.curScene.frameList) == 0:
                    diffTime = 0
                else:
                    diffTime = curTime - self.curScene.frameList[-1].timestamp  ## timestamp from last Frame

                print(diffTime)

                self.curScene.addFrame(Frame(packet.dmxData, curTime, diffTime))

        receiver.start()
        receiver.join_multicast(1)

        # sleep til signal received and handler ist triggerd
        while self.dataAction and self.running:
            signal.pause()

        print("[REC] stop recording")
        ## put scene in db
        self.curScene.putSceneInDb(self.db)

        # allow nex recording
        cur = self.db.cursor()
        cur.execute("""UPDATE util
                       SET scene = ?
                       WHERE name = ?""", (Dmx.SCENE_NONE, Dmx.REC_NAME))
        self.db.commit()

        receiver.leave_multicast(1)
        receiver.stop()


class Playback(BackgroundProcess):
    notifyFlag = False

    def __init__(self):
        self.processName = Dmx.PLAY_NAME

    sender: sacn.sACNsender

    def sigHandlerStart(self, signum, frame):
        self.notifyFlag = True

    def shutdownHandler(self, signum, frame):
        super().shutdownHandler(signum, frame)
        # sender stop when shutdown
        self.sender.stop()

    @override
    def loop(self, databasePath: str):
        super().setup(databasePath)

        self.sender = sacn.sACNsender()
        self.sender.start()
        self.sender.activate_output(2)
        self.sender[2].multicast = True

        # TODO: load default scene at startup in db with empty data

        # TODO: Static scene

        # default scene laden
        self.curScene = self.loadSceneFromDB()

        while self.running:
            self.playback()
            if self.notifyFlag:
                self.curScene = self.loadSceneFromDB()
                self.notifyFlag = False

    def loadSceneFromDB(self) -> Scene:
        # get scene out of db
        cur = self.db.cursor()
        name = cur.execute("""SELECT scene
                              FROM util
                              WHERE name == ?""", (Dmx.PLAY_NAME,)).fetchone()['scene']

        # check if scene exists
        exists = cur.execute("""SELECT COUNT(*)
                                FROM frame
                                WHERE scenename = ?""", (name,)).fetchone()[0]

        if exists <= 0:
            print("[PLAY] could not find scene: " + name + " . Returning to default scene")
            default = Scene(Dmx.SCENE_NONE)
            default.getSceneOutOfDb(self.db)
            return default

        s = Scene(name)
        s.getSceneOutOfDb(self.db)
        return s

    def playback(self):

        print("[PLAY] start playback: " + self.curScene.name)

        while not self.notifyFlag and self.running:
            for frame in self.curScene.frameList:
                # QUESTION geht das auch besser mit dem scene wechseln?
                if self.notifyFlag:
                    print("[PLAY] stop playback: " + self.curScene.name)
                    return
                # print(frame.timeAfterPrevious)
                # print(frame.DmxUniverseData)
                try:
                    time.sleep(frame.timeAfterPrevious)
                except InterruptedError:
                    # TODO: test this
                    return
                self.sender[2].dmx_data = frame.DmxUniverseData

        print("returned normally")


def startAsProcess(databasePath: str):
    contextMultiprocessing = mp.get_context('fork')
    rec = Recording()
    play = Playback()
    runningProcess1 = contextMultiprocessing.Process(target=rec.loop, daemon=True, args=(databasePath,))
    runningProcess2 = contextMultiprocessing.Process(target=play.loop, daemon=True, args=(databasePath,))
    runningProcess1.start()
    runningProcess2.start()


def initDB(db: Connection):
    cur = db.cursor()
    dataRec = (Dmx.REC_NAME, 0, Dmx.SCENE_NONE)
    dataPlay = (Dmx.PLAY_NAME, 0, Dmx.SCENE_NONE)
    cur.execute(
        "INSERT INTO util VALUES (?, ?, ?)", dataRec)
    cur.execute(
        "INSERT INTO util VALUES (?, ?, ?)", dataPlay)
    db.commit()


if __name__ == '__main__':
    # only for development and testing
    # Recording().loop("/home/max/PycharmProjects/DmxWebPlayer/instance/flaskr.sqlite")
    startAsProcess("/home/max/PycharmProjects/DmxWebPlayer/instance/flaskr.sqlite")
    while True:
        time.sleep(1)
# Playback("/home/max/PycharmProjects/DmxWebPlayer/instance/flaskr.sqlite")
