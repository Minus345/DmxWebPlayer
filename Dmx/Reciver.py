import time
import sacn

from Dmx.Frame import Frame
from Dmx.Scene import Scene


def createScene(name: str):
    CurScene = Scene(name)
    return CurScene


def receive(scene: Scene):
    # provide an IP-Address to bind to if you want to receive multicast packets from a specific interface
    receiver = sacn.sACNreceiver()
    receiver.start()  # start the receiving thread

    diffTime = time.time()

    @receiver.listen_on('universe', universe=1
    def callback(packet):  # packet type: sacn.DataPacket
        if packet.dmxStartCode == 0x00:  # ignore non-DMX-data packets
            curTime = time.time()
            print(packet.dmxData)
            scene.addFrame(Frame(packet.dmxData, diffTime - curTime))

    # optional: if multicast is desired, join with the universe number as parameter
    receiver.join_multicast(1)

    time.sleep(10)  # receive for 10 seconds

    # optional: if multicast was previously joined
    receiver.leave_multicast(1)

    receiver.stop()


if __name__ == "__main__":
    receive()
