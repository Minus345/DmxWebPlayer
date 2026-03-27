from typing import List

from Dmx.Frame import Frame


class Scene:
    name: str
    running = False
    frameList: List[Frame] = list()

    def __init__(self, name):
        self.name = name

    def addFrame(self, frame: Frame):
        self.frameList.append(frame)
