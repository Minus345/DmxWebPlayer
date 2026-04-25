import sqlite3

from db import get_db

TABLE_SCENE = "scene"
TABLE_FRAME = "frame"


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
