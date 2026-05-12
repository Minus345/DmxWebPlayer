import os
import signal

from flask import Flask, request
from flask import render_template
from flask_socketio import SocketIO, emit

import Dmx
import db

app = Flask(__name__, instance_relative_config=True)
# create and configure the app
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)
# configure websocket
socketio = SocketIO(app)
# ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)
# setup db
db.init_app(app)
# start Recording and Playback Processes
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
Dmx.startBackgroundProcesses(app.config['DATABASE'])


@app.route('/')
def index():
    return render_template('playback.html', curRecording=Dmx.getCurrantRecording(db.get_db()), sceneList=Dmx.getCurrantScenes(db.get_db()), log="started ...")


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        if request.form.get('sceneName') is not None:
            sceneName = request.form.get('sceneName')
            # scene Name is empty
            if sceneName == '':
                return render_template('sceneCreationError.html', error="No scene name provided")

            if request.form.get('static') is not None and request.form.get('static') == 'True':
                Dmx.startRecordingNewScene(sceneName, True)
            Dmx.startRecordingNewScene(sceneName)

        elif request.form.get('status') == 'stop':
            Dmx.stopRecordingNewScene()

        elif request.form.get('edit') is not None:
            pass

        elif request.form.get('delete') is not None:
            Dmx.deleteScene(db.get_db(), int(request.form.get('delete')))

    return render_template('edit.html', curRecording=Dmx.getCurrantRecording(db.get_db()), sceneList=Dmx.getCurrantScenes(db.get_db()))


@app.route('/playback', methods=['GET', 'POST'])
def playback():
    return render_template('playback.html')


@socketio.on('start')
def startScene(data):
    print('start: ' + str(data))
    if data == -1:
        Dmx.stopPlayer()
    else:
        Dmx.startPlayer(int(data))

    emit('active', data, broadcast=True)


@socketio.on('connect')
def handle_connect():
    emit('init_scenes', {"scenes": Dmx.getCurrantScenes(db.get_db())})


if __name__ == '__main__':
    socketio.run(app)
