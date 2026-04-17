from typing import Any

import Dmx
import db
from db import get_db


def getCurrantScenes() -> list[Any]:
    cur = get_db().cursor()
    sceneListRow = cur.execute("""SELECT scenename
                                  FROM frame
                                  WHERE frameid = 0""").fetchall()
    sceneList = list(map(lambda x: x[0], sceneListRow))

    return sceneList

def deleteScene(sceneName: str):
    cur = get_db().cursor()
    cur.execute("""DELETE FROM frame WHERE scenename = ?""", (sceneName,))
    get_db().commit()


def getCurrantRecording():
    cur = get_db().cursor()
    curRecording = cur.execute("""SELECT scene
                                  FROM util
                                  WHERE name = ?""", (Dmx.REC_NAME,)).fetchone()[0]
    return curRecording


def getPidFromProcess(name: str) -> Any:
    if name != Dmx.REC_NAME and name != Dmx.PLAY_NAME:
        raise Exception("Invalid Process Name")

    cur = get_db().cursor()
    pidReceiverProcess = cur.execute("""SELECT pid
                                        FROM util
                                        WHERE name == ?""", (name,)).fetchone()['pid']
    return pidReceiverProcess

def updateUtilDbSceneName(name: str, sceneName: str):
    cur = get_db().cursor()
    cur.execute("""UPDATE util
                   SET scene = ?
                   WHERE name = ?""", (sceneName, name))
    get_db().commit()