import sacn


class Frame:
    timeAfterPrevious = 0.0
    DmxUniverseData = sacn.DataPacket

    def __init__(self,data:sacn.DataPacket,timeAfterPrevious):
        self.timeAfterPrevious = timeAfterPrevious
        self.DmxUniverseData = data
