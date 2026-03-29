from traceback import print_tb
from typing import List

from flask import Flask, request
from Dmx import Reciver
from Dmx import Scene
from flask import render_template

app = Flask(__name__)

sceneList: List[Scene] = list()
global curDmxReceiver
global curDmxSender


@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.form)
    if request.method == 'POST':
        if request.form.get('Start-Recording') == 'Start-Recording':
            startReceiving()
            return render_template('index.html', var="Recording running...")
    elif request.form == 'GET':
        print("get")
    return render_template('index.html', var="hi")


# @app.route('/startReceiving')
def startReceiving():
    global curDmxReceiver
    curDmxReceiver = Reciver.DmxReceiver("name")
    curDmxReceiver.startRecording()
    return 'startReceiving'


@app.route('/stopReceiving')
def stopReceiving():
    sceneList.append(curDmxReceiver.stopRecording())
    return 'stopReceiving'


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


if __name__ == '__main__':
    app.run()
