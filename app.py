import os
import signal
from selectors import SelectSelector
from typing import List

from flask import Flask, request, g, current_app

import Dmx.Reciver
from Dmx import Reciver
from Dmx.StoreDmxData import Scene
from flask import render_template

from db import get_db

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)
# ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)
import db

db.init_app(app)

Dmx.Reciver.DmxReceiver(app.config['DATABASE'])

sceneList: List[Scene] = list()
curRecording = False
global curDmxReceiver
global curDmxSender

# TODO SIGHILD abfangen

REC_NAME = "rec"


@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.form)
    if request.method == 'POST':

        cur = get_db().cursor()
        pidReceiverProcess = cur.execute("""SELECT pid
                                            FROM util
                                            WHERE name == ?""", (REC_NAME,)).fetchone()['pid']

        if request.form.get('sceneName') is not None:
            sceneName = request.form.get('sceneName')
            #scnenName is empty
            if sceneName == '':
                return render_template('sceneCreationError.html', error="No scene name provided")

            #scnenName already exists
            exists = cur.execute("""SELECT COUNT(1)
                                    FROM frame
                                    WHERE scenename = ?""", (sceneName,)).fetchone()[0]
            if exists == 1:
                return render_template('sceneCreationError.html', error="Scene already exists")

            cur.execute("""UPDATE util
                           SET scene = ?
                           WHERE name = ?""", (sceneName, REC_NAME))
            get_db().commit()
            # start recording
            os.kill(pidReceiverProcess, signal.SIGUSR1)

        elif request.form.get('status') == 'stop':
            # stop recording
            os.kill(pidReceiverProcess, signal.SIGUSR2)

    elif request.form == 'GET':
        print("get")
    return render_template('index.html', sceneList=sceneList, curRecording=curRecording)


@app.route('/playback', methods=['GET', 'POST'])
def playback():
    print(request.form)
    return render_template('index.html', sceneList=sceneList, curRecording=curRecording)


@app.route('/startPlayback')
def startPlayback():
    global curDmxSender
    curDmxSender = Reciver.DmxPlayback(sceneList[0])
    curDmxSender.startPlayback()
    return 'startPlayback'


@app.route('/stopPlayback')
def stopPlayback():
    curDmxSender.stopPlayback()
    return 'stopPlayback'


@app.route('/setup')
def setup():
    sceneList.append(Scene("a"))
    sceneList.append(Scene("b"))
    sceneList.append(Scene("c"))
    print(sceneList)
    cur = get_db().cursor()
    cur.execute("""INSERT INTO state
                   VALUES ('b', 1)""")
    get_db().commit()
    get_db().close()
    return 'setup'


@app.route('/get')
def get():
    cur = get_db().cursor()
    res = cur.execute("""SELECT *
                         FROM state
                         WHERE status == 'a'""")
    b = res.fetchone()
    print(b.keys())
    print(b['status'])
    print(b['value'])
    get_db().close()
    return 'a'


if __name__ == '__main__':
    app.run()
