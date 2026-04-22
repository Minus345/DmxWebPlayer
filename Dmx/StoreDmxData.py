import pickle
from sqlite3 import Connection


class Frame:
    def __init__(self, data: list[int]):
        self.DmxUniverseData = data
        self.step = 0

    def setTimeAfterPrevious(self, timeAfterPrevious: float):
        self.step = round(timeAfterPrevious / 0.03)  # TODO magic value


def getFrameInDbFormat(frame: Frame) -> bytes:
    return pickle.dumps(frame.DmxUniverseData)


def getFrameInObjectFormat(data) -> list[int]:
    return pickle.loads(data)


class Scene:
    def __init__(self, name: str, frameList=None, sceneId=None):
        self.name = name
        if frameList is None:
            frameList = list()
        self.frameList: list[Frame] = frameList
        self.frameCounter = 0
        self.sleepCounter = 0
        self.id = sceneId

    @classmethod
    def createNew(cls, name):
        return cls(name=name)

    @classmethod
    def loadFromDB(cls, sceneID: int, db: Connection):
        cur = db.cursor()
        name = cur.execute("SELECT name FROM scene WHERE id = ?", (sceneID,)).fetchone()[0]  # TODO error handling db
        frameCount = cur.execute("SELECT COUNT(*) FROM frame WHERE scene = ?", (sceneID,)).fetchone()[0]
        frameList = list[Frame]()
        for i in range(0, frameCount):
            frameData = cur.execute("SELECT * FROM frame WHERE scene = ? AND count = ?", (sceneID, i,)).fetchone()
            frame = Frame(getFrameInObjectFormat(frameData['data']))
            frame.step = frameData['timestamp']
            frameList.append(frame)
        return cls(name=name, frameList=frameList, sceneId=sceneID)

    def addFrame(self, frame: Frame):
        self.frameList.append(frame)

    def dbCreateScene(self, db: Connection):
        cur = db.cursor()
        cur.execute("INSERT INTO scene VALUES (NULL,?)", (self.name,))
        self.id = cur.lastrowid
        db.commit()

    def dbInsertDmxData(self, db: Connection):
        cur = db.cursor()
        for i in range(0, len(self.frameList)):
            data = (self.id, i, self.frameList[i].step, getFrameInDbFormat(self.frameList[i]))
            cur.execute(
                "INSERT INTO frame VALUES (NULL,?,?,?,?)", data)
        db.commit()

    def apply(self, output: list[int]):
        self.sleepCounter += 1
        if self.sleepCounter >= self.frameList[self.frameCounter].step:
            for ch, vl in zip(range(0, 255), self.frameList[self.frameCounter].DmxUniverseData):
                output[ch] = vl
            self.frameCounter += 1
            self.sleepCounter = 0
            if self.frameCounter >= len(self.frameList):
                self.frameCounter = 0
