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
    return render_template('playback.html')


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    return render_template('edit.html')

@socketio.on('connect', namespace='/edit')
def handle_connect():
    emit('init_scenes', {"scenes": Dmx.getCurrantScenes(db.get_db())})


@socketio.on('startRecording', namespace='/edit')
def startScene(data):
    print('start: ' + str(data))
    pass

@socketio.on('stopRecording', namespace='/edit')
def stopScene():
    print('stop')
    pass

@socketio.on('edit', namespace='/edit')
def editScene(data):
    print('edit: ' + str(data))
    pass

@socketio.on('delete', namespace='/edit')
def deleteScene(data):
    print('delete: ' + str(data))
    pass

'''

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

'''


@app.route('/playback')
def playback():
    return render_template('playback.html')


@socketio.on('start', namespace='/playback')
def startScene(data):
    print('start: ' + str(data))
    if data == -1:
        Dmx.stopPlayer()
    else:
        Dmx.startPlayer(int(data))

    emit('active', data, broadcast=True)


@socketio.on('connect', namespace='/playback')
def handle_connect():
    emit('init_scenes', {"scenes": Dmx.getCurrantScenes(db.get_db())})


if __name__ == '__main__':
    socketio.run(app)
