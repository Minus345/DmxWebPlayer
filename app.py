import os
from typing import List

from flask import Flask, request
from Dmx import Reciver
from Dmx.Scene import Scene
from flask import render_template

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

sceneList: List[Scene] = list()
curRecording = False
global curDmxReceiver
global curDmxSender


@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.form)
    if request.method == 'POST':
        if request.form.get('sceneName') is not None:
            sceneName = request.form.get('sceneName')
            if sceneName == '':
                return render_template('sceneCreationError.html', error="No scene name provided")

            global curDmxReceiver
            curDmxReceiver = Reciver.DmxReceiver(sceneName)
            curDmxReceiver.startRecording()

        elif request.form.get('status') == 'stop':
            if 'curDmxReceiver' in globals():
                sceneList.append(curDmxReceiver.stopRecording())
            else:
                return render_template('sceneCreationError.html', error='DmxReceiver is not defined')

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
    return 'setup'


if __name__ == '__main__':
    app.run()
