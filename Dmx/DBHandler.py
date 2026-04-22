import sqlite3
from typing import Any

import Dmx
from db import get_db

# TODO move into DMX module

TABLE_SCENE = "scene"
TABLE_FRAME = "frame"
TABLE_UTIL = "util"

"""
DB Documentation:
Util: 
    name pid scene
    rec  x   :str (name)
    play x   :int (id)
"""


class DBHandler:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.cur = self.db.cursor()

    def getCurrantScenes(self) -> list[tuple[int, int]]:
        sceneListRow = self.cur.execute("""SELECT *
                                      FROM scene""").fetchall()
        sceneList: list[tuple[int, int]] = []
        for row in sceneListRow:
            sceneList.append((row["id"], row["name"]))
        return sceneList

    def deleteScene(self, sceneId: int):
        self.cur.execute("""DELETE
                       FROM scene
                       WHERE id = ?""", (sceneId,))
        get_db().commit()

    def getCurrantUtilName(self, name:str):
        """:returns the vale currently in db "util" -> "rec" wich is the current scene name or "play" is the scene id"""
        curRecording = self.cur.execute("""SELECT scene
                                      FROM util
                                      WHERE name = ?""", (name,)).fetchone()[0]
        return curRecording

    def updateUtilDbSceneName(self, name: str, sceneId: int):
        self.cur.execute("""UPDATE util
                       SET scene = ?
                       WHERE name = ?""", (sceneId, name))
        self.db.commit()

    def getPidFromProcess(self, name: str) -> Any:
        if name != Dmx.REC_NAME and name != Dmx.PLAY_NAME:
            raise Exception("Invalid Process Name")

        pidReceiverProcess = self.cur.execute("""SELECT pid
                                            FROM util
                                            WHERE name == ?""", (name,)).fetchone()['pid']
        return pidReceiverProcess

    def getNameFromID(self, id: int) -> str:
        return self.cur.execute("""SELECT name FROM scene WHERE id = ?""", (id,)).fetchone()[0]
