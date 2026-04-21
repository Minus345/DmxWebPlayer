import os
import signal

from flask import Flask, request
from flask import render_template

import Dmx.ManageDmxData
import dbQuery
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
#check if db file exsists
Dmx.ManageDmxData.startAsProcess(app.config['DATABASE'])


# TODO make init db command work -> delay startup Processes


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    print(request.form)
    if request.method == 'POST':
        pidReceiverProcess = dbQuery.getPidFromProcess(Dmx.REC_NAME)
        if request.form.get('sceneName') is not None:
            sceneName = request.form.get('sceneName')
            # scene Name is empty
            if sceneName == '':
                return render_template('sceneCreationError.html', error="No scene name provided")

            # scene Name already exists
            cur = get_db().cursor()
            exists = cur.execute("""SELECT COUNT(*)
                                    FROM frame
                                    WHERE scenename = ?""", (sceneName,)).fetchone()[0]
            if exists >= 1:
                return render_template('sceneCreationError.html', error="Scene already exists")

            dbQuery.updateUtilDbSceneName(Dmx.REC_NAME, sceneName)
            # start recording
            os.kill(pidReceiverProcess, signal.SIGUSR1)

        elif request.form.get('status') == 'stop':
            # stop recording
            os.kill(pidReceiverProcess, signal.SIGUSR2)

        elif request.form.get('edit') is not None:
            pass

        elif request.form.get('delete') is not None:
            dbQuery.deleteScene(request.form.get('delete'))

    return render_template('edit.html', curRecording=dbQuery.getCurrantRecording(), sceneList=dbQuery.getCurrantScenes())


@app.route('/playback', methods=['GET', 'POST'])
def playback():
    print(request.form)
    if request.method == 'POST':
        start = request.form.get('start')
        stop = request.form.get('stop')
        if start is not None:
            # start scene in <start>
            # check if scene is really in db -> in ManageDmxData
            dbQuery.updateUtilDbSceneName(Dmx.PLAY_NAME, start)
        if stop is not None:
            # start default scene
            dbQuery.updateUtilDbSceneName(Dmx.PLAY_NAME, Dmx.SCENE_NONE)

        pidReceiverProcess = dbQuery.getPidFromProcess(Dmx.PLAY_NAME)
        os.kill(pidReceiverProcess, signal.SIGUSR1)
    return render_template('playback.html', sceneList=dbQuery.getCurrantScenes())
