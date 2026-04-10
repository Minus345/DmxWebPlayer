import os
import signal

from flask import Flask, request
from flask import render_template

import Dmx.ManageDmxData
from db import get_db

app = Flask(__name__, instance_relative_config=True)
# create and configure the app
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)
# ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)
import db

db.init_app(app)

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

# start Recording and Playback Threads
Dmx.ManageDmxData.startAsProcess(app.config['DATABASE'])


def renderBasicTemplate() -> str:
    cur = get_db().cursor()
    sceneListRow = cur.execute("""SELECT scenename
                                  FROM frame
                                  WHERE frameid = 0""").fetchall()
    sceneList = list(map(lambda x: x[0], sceneListRow))

    curRecording = cur.execute("""SELECT scene
                                  FROM util
                                  WHERE name = ?""", (Dmx.REC_NAME,)).fetchone()[0]

    return render_template('index.html', sceneList=sceneList, curRecording=curRecording)


@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.form)
    if request.method == 'POST':

        cur = get_db().cursor()
        pidReceiverProcess = cur.execute("""SELECT pid
                                            FROM util
                                            WHERE name == ?""", (Dmx.REC_NAME,)).fetchone()['pid']

        if request.form.get('sceneName') is not None:
            sceneName = request.form.get('sceneName')
            # scnenName is empty
            if sceneName == '':
                return render_template('sceneCreationError.html', error="No scene name provided")

            # scnenName already exists
            exists = cur.execute("""SELECT COUNT(1)
                                    FROM frame
                                    WHERE scenename = ?""", (sceneName,)).fetchone()[0]
            if exists >= 1:
                return render_template('sceneCreationError.html', error="Scene already exists")

            cur.execute("""UPDATE util
                           SET scene = ?
                           WHERE name = ?""", (sceneName, Dmx.REC_NAME))
            get_db().commit()
            # start recording
            os.kill(pidReceiverProcess, signal.SIGUSR1)

        elif request.form.get('status') == 'stop':
            # stop recording
            os.kill(pidReceiverProcess, signal.SIGUSR2)
            return renderBasicTemplate()

    elif request.form == 'GET':
        print("get")
    return renderBasicTemplate()


@app.route('/playback', methods=['GET', 'POST'])
def playback():
    print(request.form)
    if request.method == 'POST':
        start = request.form.get('start')
        stop = request.form.get('stop')
        if start is not None:
            # start scene in <start>
            #TODO check if scene is really in db
            updateUtilDbSceneName(Dmx.PLAY_NAME, start)
        if stop is not None:
            # start default scene
            updateUtilDbSceneName(Dmx.PLAY_NAME, Dmx.SCENE_NONE)

        cur = get_db().cursor()
        pidReceiverProcess = cur.execute("""SELECT pid
                                            FROM util
                                            WHERE name == ?""", (Dmx.PLAY_NAME,)).fetchone()['pid']
        os.kill(pidReceiverProcess, signal.SIGUSR1)

    return renderBasicTemplate()


def updateUtilDbSceneName(name: str, sceneName: str):
    cur = get_db().cursor()
    cur.execute("""UPDATE util
                   SET scene = ?
                   WHERE name = ?""", (sceneName, name))
    get_db().commit()