import multiprocessing as mp
import signal
import sqlite3
import sys
import threading
import time
from itertools import count
from multiprocessing.connection import Pipe
from threading import Thread

import sacn

import Dmx
from Dmx.StoreDmxData import Scene, Frame


def setupDbConnection(databasePath: str):
    # TODO merge with db.get_db()
    db = sqlite3.connect(
        databasePath,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    return db


class Recording:
    def __init__(self, databasePath: str, pipe):
        self.db = setupDbConnection(databasePath)
        self.curScene = None
        self.pipe = pipe
        self.prevTimeStamp = 0.0
        self.dbHandler = Dmx.DBHandler(self.db)
        self.running = True

        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        while self.running:
            data = pipe.recv()
            if data[0] == Dmx.POISONING:
                break
            if data[0] == Dmx.START_REC:
                self.recordDmx(data[1], data[2])

        pipe.close()
        print("[REC] off")
        sys.exit(0)

    def recordDmx(self, sceneName: str, static: bool):
        self.curScene = Scene(sceneName, static=static)
        self.curScene.dbCreateScene(self.db)

        ## start recording
        print("[REC] start recording: " + sceneName)

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

        while True:
            data = self.pipe.recv()
            if data[0] == Dmx.POISONING:
                self.running = False
                break
            if data[0] == Dmx.STOP_REC:
                break
            else:
                print("[REC] currently recording: " + sceneName)

        print("[REC] stop recording")
        receiver.leave_multicast(1)
        receiver.stop()

        if len(self.curScene.frameList) != 0:
            # only save first frame when scene is static
            if self.curScene.static:
                firstElement = self.curScene.frameList[0]
                self.curScene.frameList = [firstElement, ]
            self.curScene.dbInsertDmxData(self.db)
        else:
            print("[REC] scene has no data")


class Playback:
    TARGET_HZ = 30
    PERIOD = 1.0 / TARGET_HZ

    def __init__(self, databasePath: str, pipe):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.db = setupDbConnection(databasePath)
        self.running = True
        self.pipe = pipe
        self.curSceneLock = threading.Lock()

        self.defaultScene = Scene("Default Scene", static=True)
        self.defaultScene.addFrame(Frame([0] * 512))
        self.curScene = self.defaultScene

        self.sender = sacn.sACNsender(fps=self.TARGET_HZ)
        self.senderThread = Thread(target=self.senderWorker, args=(), daemon=True)
        self.senderThread.start()

        while self.running:
            pipeData = self.pipe.recv()

            """
            pipeData values:
            - scene id :int
            - POISONING
            - STOP_PLAY
            """

            if pipeData == Dmx.POISONING:
                break
            elif pipeData == Dmx.STOP_PLAY:
                with self.curSceneLock:
                    self.curScene = self.defaultScene
            else:
                exists = self.db.execute("""SELECT COUNT(*)FROM scene WHERE id = ?""", (pipeData,)).fetchone()[0]
                if exists == 0:
                    pipe.send("Couldn't find scene, pleas refresh your browser")
                    continue

                nextScene = Scene.loadFromDB(pipeData, self.db)
                if len(nextScene.frameList) == 0:
                    pipe.send("scene has no data")
                    continue

                pipe.send(f"starting scene: {nextScene.name}")
                with self.curSceneLock:
                    self.curScene = nextScene

        self.sender.stop()
        self.pipe.close()
        sys.exit(0)

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


def startAsProcess(databasePath: str):
    parentConnRec, childConnRec = Pipe()
    parentConnPlay, childConnPlay = Pipe()
    contextMultiprocessing = mp.get_context('fork')
    runningProcess1 = contextMultiprocessing.Process(target=Recording, daemon=True, args=(databasePath, childConnRec,))
    runningProcess2 = contextMultiprocessing.Process(target=Playback, daemon=True, args=(databasePath, childConnPlay))
    runningProcess1.start()
    runningProcess2.start()
    return parentConnRec, parentConnPlay
