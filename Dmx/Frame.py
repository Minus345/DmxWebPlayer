import sacn


class Frame:
    timeAfterPrevious: float
    timestamp: float
    DmxUniverseData = sacn.DataPacket

    def __init__(self, data: sacn.DataPacket, timestamp: float, timeAfterPrevious: float):
        self.timeAfterPrevious = timeAfterPrevious
        self.DmxUniverseData = data
        self.timestamp = timestamp
