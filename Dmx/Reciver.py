import queue
import time
from threading import Thread

import sacn

from Dmx.Frame import Frame
from Dmx.Scene import Scene


class DmxReceiver:
    threadingQueue: queue.Queue
    scene: Scene
    receiver: sacn.sACNreceiver

    _poisonPill = object()

    def __init__(self, name: str):
        self.threadingQueue = queue.Queue()
        self.scene = Scene(name)
        self.receiver = sacn.sACNreceiver(bind_address='192.168.188.20')

    def startRecording(self):
        """ starts the reiver in a separate thread """
        print("start recording")
        runningThread = Thread(target=self.receiverRunner)
        runningThread.start()

    def receiverRunner(self):
        @self.receiver.listen_on('universe', universe=1)
        def callback(packet):  # packet type: sacn.DataPacket
            if packet.dmxStartCode == 0x00:  # ignore non-DMX-data packets
                curTime = time.time()
                print(packet.dmxData)

                if len(self.scene.frameList) == 0:
                    diffTime = curTime
                else:
                    diffTime = curTime - self.scene.frameList[-1].timestamp  ## timestamp from last Frame

                self.scene.addFrame(Frame(packet.dmxData, curTime, diffTime))

        self.receiver.start()
        self.receiver.join_multicast(1)

        while True:
            if self.threadingQueue.get() == self._poisonPill:
                break

        self.receiver.leave_multicast(1)
        self.receiver.stop()
        self.threadingQueue.put(self.scene)

    def stopRecording(self):
        print("stopping")
        self.threadingQueue.put(self._poisonPill)
