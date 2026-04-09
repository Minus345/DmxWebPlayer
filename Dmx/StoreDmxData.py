import pickle
from sqlite3 import Connection
from typing import List

import sacn


class Frame:
    timeAfterPrevious: float  # TODO in db int
    timestamp: float
    DmxUniverseData = sacn.DataPacket

    def __init__(self, data: sacn.DataPacket, timestamp: float, timeAfterPrevious: float):
        self.timeAfterPrevious = timeAfterPrevious
        self.DmxUniverseData = data
        self.timestamp = timestamp

    def getUniverseDataInDbFormat(self) -> bytes:
        pData = pickle.dumps(self.DmxUniverseData)
        return pData


class Scene:
    name: str
    frameList: List[Frame] = list()

    def __init__(self, name):
        self.name = name

    def addFrame(self, frame: Frame):
        self.frameList.append(frame)

    def putSceneInDb(self, db: Connection):
        cur = db.cursor()
        for i in range(0, len(self.frameList)):
            data = (self.name, i, self.frameList[i].timeAfterPrevious, self.frameList[i].getUniverseDataInDbFormat())
            cur.execute(
                "INSERT INTO frame VALUES (?, ?, ?,?)", data)
        db.commit()
