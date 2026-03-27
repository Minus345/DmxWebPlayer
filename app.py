from os.path import curdir
from typing import List
from flask import Flask
from Dmx import Reciver
from Dmx import Scene
from Dmx.Reciver import DmxReceiver

app = Flask(__name__)

sceneList = list()
global curDmxReceiver

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/startReceiving')
def startReceiving():
    global curDmxReceiver
    curDmxReceiver = Reciver.DmxReceiver("name")
    sceneList.append(curDmxReceiver.startRecording())
    return 'started'


@app.route('/stopReceiving')
def stopReceiving():
    curDmxReceiver.stopRecording()
    return 'stopped'


if __name__ == '__main__':
    app.run()
