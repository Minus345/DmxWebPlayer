import pickle
from sqlite3 import Connection
from typing import List

import sacn


class Frame:
    def __init__(self, data: sacn.DataPacket, timestamp: float, timeAfterPrevious: float):
        self.timeAfterPrevious = timeAfterPrevious
        self.DmxUniverseData = data
        self.timestamp = timestamp


def getUniverseDataInDbFormat(frame: Frame) -> bytes:
    return pickle.dumps(frame.DmxUniverseData)


def getUniverseDataInObjectFormat(data) -> sacn.DataPacket:
    return pickle.loads(data)


class Scene:
    def __init__(self, name):
        self.name = name
        self.frameList: List[Frame] = list()

    def addFrame(self, frame: Frame):
        self.frameList.append(frame)

        # TODO put object directly in db wie SQLAlchemy

    def putSceneInDb(self, db: Connection):
        cur = db.cursor()
        for i in range(0, len(self.frameList)):
            data = (self.name, i, self.frameList[i].timeAfterPrevious, getUniverseDataInDbFormat(self.frameList[i]))
            cur.execute(
                "INSERT INTO frame VALUES (?, ?, ?,?)", data)
        db.commit()

    def getSceneOutOfDb(self, db: Connection):
        """load scene from db. Create empty scene first, this only appends all frames found in the db"""
        cur = db.cursor()
        frameCount = cur.execute("SELECT COUNT(*) FROM frame WHERE scenename = ?", (self.name,)).fetchone()[0]
        for i in range(0, frameCount):
            frame = cur.execute("SELECT * FROM frame WHERE scenename = ? AND frameid = ?", (self.name, i,)).fetchone()
            self.frameList.append(Frame(getUniverseDataInObjectFormat(frame['dmxdata']), 0,
                                        frame['timestamp']))
