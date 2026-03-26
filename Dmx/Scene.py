from Dmx.Frame import Frame


class Scene:
    name = str
    running = False
    frameList = [Frame]

    def __init__(self,name):
        self.name = name

    def addFrame(self,frame:Frame):
        self.frameList.append(frame)