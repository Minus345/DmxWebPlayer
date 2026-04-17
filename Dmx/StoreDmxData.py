import pickle
from sqlite3 import Connection
from typing import List


class Frame:
    def __init__(self, data: list[int]):
        self.DmxUniverseData = data
        self.step = 0

    def setTimeAfterPrevious(self, timeAfterPrevious: float):
        self.step = round(timeAfterPrevious / 0.03)


def getFrameInDbFormat(frame: Frame) -> bytes:
    return pickle.dumps(frame.DmxUniverseData)


def getFrameInObjectFormat(data) -> list[int]:
    return pickle.loads(data)


class Scene:
    def __init__(self, name):
        self.name = name
        self.frameList: List[Frame] = list()
        self.frameCounter = 0
        self.sleepCounter = 0

    def addFrame(self, frame: Frame):
        self.frameList.append(frame)

        # TODO put object directly in db wie SQLAlchemy

    def putSceneInDb(self, db: Connection):
        cur = db.cursor()
        for i in range(0, len(self.frameList)):
            data = (self.name, i, self.frameList[i].step, getFrameInDbFormat(self.frameList[i]))
            cur.execute(
                "INSERT INTO frame VALUES (?, ?, ?,?)", data)
        db.commit()

    def getSceneOutOfDb(self, db: Connection):
        """load scene from db. Create empty scene first, this only appends all frames found in the db"""
        cur = db.cursor()
        frameCount = cur.execute("SELECT COUNT(*) FROM frame WHERE scenename = ?", (self.name,)).fetchone()[0]
        for i in range(0, frameCount):
            frameData = cur.execute("SELECT * FROM frame WHERE scenename = ? AND frameid = ?", (self.name, i,)).fetchone()
            frame = Frame(getFrameInObjectFormat(frameData['dmxdata']))
            frame.step = frameData['timestamp']
            self.frameList.append(frame)


    def apply(self, output: list[int]):
        self.sleepCounter += 1
        if self.sleepCounter >= self.frameList[self.frameCounter].step:
            for ch, vl in zip(range(0, 255), self.frameList[self.frameCounter].DmxUniverseData):
                output[ch] = vl
            self.frameCounter += 1
            self.sleepCounter = 0
            if self.frameCounter >= len(self.frameList):
                self.frameCounter = 0
