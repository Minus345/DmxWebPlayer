import os
import signal

from flask import Flask, request
from flask import render_template

import Dmx

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
Dmx.startBackgroundProcesses(app.config['DATABASE'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    print(request.form)
    if request.method == 'POST':
        editor = Dmx.Editor(db.get_db())
        if request.form.get('sceneName') is not None:
            sceneName = request.form.get('sceneName')
            # scene Name is empty
            if sceneName == '':
                return render_template('sceneCreationError.html', error="No scene name provided")
            editor.startRecordingNewScene(sceneName)

        elif request.form.get('status') == 'stop':
            editor.stopRecordingNewScene()

        elif request.form.get('edit') is not None:
            pass

        elif request.form.get('delete') is not None:
            editor.deleteScene(int(request.form.get('delete')))

    return render_template('edit.html', curRecording=Dmx.Viewer(db.get_db()).getCurrantRecording(), sceneList=Dmx.Viewer(db.get_db()).getCurrantScenes())

@app.route('/playback', methods=['GET', 'POST'])
def playback():
    print(request.form)
    if request.method == 'POST':
        start = request.form.get('start')
        stop = request.form.get('stop')
        if start is not None:
            Dmx.Player(db.get_db()).startPlayer(int(start))

        if stop is not None:
            Dmx.Player(db.get_db()).stopPlayer()

    return render_template('playback.html', sceneList=Dmx.Viewer(db.get_db()).getCurrantScenes())
