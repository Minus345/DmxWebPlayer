import multiprocessing as mp
import os
import signal
import sqlite3
import sys
import threading
import time
import warnings
from sqlite3 import Connection
from threading import Thread

import sacn

import Dmx
from Dmx.StoreDmxData import Scene, Frame


# TODO hier robuste db abfragen

class BackgroundProcess:
    def __init__(self, processName: str, databasePath: str):
        """Sets Up DB wit pid - call in process"""
        self.curScene = None
        self.processName = processName
        self.dataAction = False
        self.running = True

        ## init db
        # TODO merge with db.get_db()
        self.db = sqlite3.connect(
            databasePath,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON;")
        cur = self.db.cursor()

        # check if db is initialized
        try:
            isInitialized = cur.execute("SELECT COUNT(*) FROM util WHERE name = ?", (self.processName,)).fetchone()[0]
            if isInitialized <= 0:
                warnings.warn(message='DB not initialised with values. Disabling Dmx: ' + processName + ' pleas init db', category=Warning)
                sys.exit(1)
        except sqlite3.OperationalError:
            warnings.warn(message='DB not initialised with tables.  Disabling Dmx: ' + processName + ' pleas init db', category=Warning)
            sys.exit(1)

        # put ip data in util table
        data = (os.getpid(), Dmx.SCENE_NONE, self.processName)
        cur.execute(
            "UPDATE util SET pid = ?, scene = ? WHERE name = ?", data)
        self.db.commit()

        signal.signal(signal.SIGUSR1, self.sigHandlerStart)
        signal.signal(signal.SIGUSR2, self.sigHandlerStop)
        signal.signal(signal.SIGTERM, self.shutdownHandler)
        signal.signal(signal.SIGINT, self.shutdownHandler)

    def sigHandlerStart(self, signum, frame):
        self.dataAction = True

    def sigHandlerStop(self, signum, frame):
        self.dataAction = False

    def shutdownHandler(self, signum, frame):
        print(f"shutdown {self.processName}")
        self.running = False


class Recording(BackgroundProcess):
    def __init__(self, databasePath: str):
        super().__init__(Dmx.REC_NAME, databasePath)
        self.prevTimeStamp = 0.0
        self.dbHandler = Dmx.DBHandler(self.db)

        while self.running:
            signal.pause()
            if self.dataAction:
                self.recordDmx()

    def recordDmx(self):
        ## get scene name from db or shutdown request
        name = self.dbHandler.getCurrantUtilName(Dmx.REC_NAME)

        if name == Dmx.SCENE_NONE:
            print("[REC] no scene name defined")
            self.dataAction = False
            return
        self.curScene = Scene(name)
        self.curScene.dbCreateScene(self.db)

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
                    diffTime = curTime - self.prevTimeStamp  ## timestamp from last Frame

                print(f"{diffTime} + {diffTime / 0.03} +{round(diffTime / 0.03)}")

                frame = Frame(packet.dmxData)
                frame.setTimeAfterPrevious(diffTime)
                self.curScene.addFrame(frame)
                self.prevTimeStamp = curTime

        receiver.start()
        receiver.join_multicast(1)

        # sleep til signal received and handler ist triggerd
        while self.dataAction and self.running:
            signal.pause()

        print("[REC] stop recording")
        receiver.leave_multicast(1)
        receiver.stop()

        if len(self.curScene.frameList) != 0:
            ## put scene in db
            self.curScene.dbInsertDmxData(self.db)
        else:
            print("[REC] scene has no data")
        # allow next recording
        self.dbHandler.updateUtilDbSceneName(Dmx.REC_NAME, Dmx.SCENE_NONE)


class Playback(BackgroundProcess):
    # TODO: Static scene
    TARGET_HZ = 30
    PERIOD = 1.0 / TARGET_HZ

    def sigHandlerStart(self, signum, frame):
        self.notifyFlag = True

    def shutdownHandler(self, signum, frame):
        super().shutdownHandler(signum, frame)
        # sender stop when shutdown
        self.sender.stop()

    def __init__(self, databasePath: str):
        super().__init__(Dmx.PLAY_NAME, databasePath)
        self.curSceneLock = threading.Lock()
        self.notifyFlag = False

        self.defaultScene = Scene("Default Scene")
        self.defaultScene.addFrame(Frame([0] * 512))
        self.curScene = self.defaultScene

        self.sender = sacn.sACNsender(fps=self.TARGET_HZ)
        self.senderThread = Thread(target=self.senderWorker, args=(), daemon=True)
        self.senderThread.start()

        while self.running:
            signal.pause()
            if self.notifyFlag:
                newScene = self.loadSceneFromDB()
                with self.curSceneLock:
                    self.curScene = newScene
                self.notifyFlag = False

    def senderWorker(self):
        self.sender.start()
        self.sender.activate_output(2)
        self.sender[2].multicast = True

        nextTime = time.perf_counter()
        output = [0] * 512
        old = [1] * 512

        while self.running:
            with self.curSceneLock:
                self.curScene.apply(output)

            # only send new data
            if output != old:
                self.sender[2].dmx_data = output
                old = output[:]

            # ---- 30 hz berechnung ----
            nextTime += self.PERIOD
            sleepTime = nextTime - time.perf_counter()
            if sleepTime > 0:
                time.sleep(sleepTime)
            else:
                # Wir sind zu langsam → Frame skippen
                nextTime = time.perf_counter()

    def loadSceneFromDB(self) -> Scene:
        curId = Dmx.DBHandler(self.db).getCurrantUtilName(Dmx.PLAY_NAME)
        if curId == Dmx.SCENE_NONE:
            return self.defaultScene
        s = Scene.loadFromDB(curId, self.db)
        return s


def startAsProcess(databasePath: str):
    contextMultiprocessing = mp.get_context('fork')
    runningProcess1 = contextMultiprocessing.Process(target=Recording, daemon=True, args=(databasePath,))
    runningProcess2 = contextMultiprocessing.Process(target=Playback, daemon=True, args=(databasePath,))
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
