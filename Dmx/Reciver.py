import os
import signal
import sqlite3
import time
import multiprocessing as mp
from os import pidfd_open
from sqlite3 import Connection
from threading import Thread

import sacn

from Dmx.StoreDmxData import Scene, Frame


class DmxReceiver:
    db: Connection
    REC_NAME = "rec"
    curRecScene: Scene

    def dummyHandler(self, signum, frame):
        pass

    def handlerStartRecordingDmx(self):
        """SIGUSR1"""
        ## get scene name from db or shutdown request
        cur = self.db.cursor()
        name = cur.execute("""SELECT scene
                              FROM util
                              WHERE name == 'rec'""").fetchone()['scene']
        self.curRecScene = Scene(name)

        ## start recording
        print("[REC] start recording: " + name)
        self.recordDmx()

    def handlerStopRecordingDmx(self):
        """SIGUSR2"""
        print("[REC] stop recording")
        ## put scene in db
        self.curRecScene.putSceneInDb(self.db)

    def __init__(self, databasePath: str):
        # TODO Sollte nur einmal gesetzt werden:
        mp.set_start_method('fork')
        runningProcess = mp.Process(target=self.setupProcess, daemon=True, args=(databasePath,))
        runningProcess.start()

    def setupProcess(self, databasePath: str):
        ## init db
        self.db = sqlite3.connect(
            databasePath,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.db.row_factory = sqlite3.Row

        cur = self.db.cursor()

        # TODO was tun wenn noch nie erstellt wurde
        cur.execute(
            "DELETE FROM util WHERE name = ?", (self.REC_NAME,))
        self.db.commit()

        data = (self.REC_NAME, os.getpid(), "NULL")
        cur.execute(
            "INSERT INTO util VALUES (?, ?, ?)", data)
        self.db.commit()

        signal.signal(signal.SIGUSR1, self.dummyHandler)
        signal.signal(signal.SIGUSR2, self.dummyHandler)

        while True:
            ## wait until SIGUSR1 is signaled
            signal.sigwait([signal.SIGUSR1])
            self.handlerStartRecordingDmx()

    def recordDmx(self):
        receiver = sacn.sACNreceiver(bind_address='192.168.188.20')

        @receiver.listen_on('universe', universe=1)
        def callback(packet):  # packet type: sacn.DataPacket
            if packet.dmxStartCode == 0x00:  # ignore non-DMX-data packets
                curTime = time.time()
                print(packet.dmxData)

                if len(self.curRecScene.frameList) == 0:
                    diffTime = 0
                else:
                    diffTime = curTime - self.curRecScene.frameList[-1].timestamp  ## timestamp from last Frame

                print(diffTime)

                self.curRecScene.addFrame(Frame(packet.dmxData, curTime, diffTime))

        receiver.start()
        receiver.join_multicast(1)

        ## wait until USR2 is signaled aka stop Recording
        signal.sigwait([signal.SIGUSR2])
        self.handlerStopRecordingDmx()

        receiver.leave_multicast(1)
        receiver.stop()


class DmxPlayback:
    scene: Scene
    sender: sacn.sACNsender
    running = False

    def __init__(self, scene: Scene):
        self.sender = sacn.sACNsender(source_name="DmxWebPlayer")
        self.scene = scene

    def startPlayback(self):
        self.sender.start()
        self.sender.activate_output(2)
        self.sender[2].multicast = True
        self.running = True

        playbackThread = Thread(target=self.playbackRunner)
        playbackThread.start()

    def playbackRunner(self):
        print("start playback")
        while self.running:
            for frame in self.scene.frameList:
                print(frame.timeAfterPrevious)
                print(frame.DmxUniverseData)
                time.sleep(frame.timeAfterPrevious)
                self.sender[2].dmx_data = frame.DmxUniverseData

    def stopPlayback(self):
        self.running = False
        self.sender.stop()
