import mediapipe as mp
import cv2
import time
import numpy as np
import keyboard
import pyvirtualcam
    
class handTracker:
    def __init__(self):
        self.__mode__ = False
        self.__maxHands__ = 1
        self.handsMp = mp.solutions.hands
        self.hands = self.handsMp.Hands()
        self.mpDraw= mp.solutions.drawing_utils
        self.indexID = 8
    
    #returns the index finger's position
    def getIndexPosition(self, frame):
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[0]
            
            lm = myHand.landmark[self.indexID]
            
            h, w, c = frame.shape
            coordinate = (int(lm.x * w), int(lm.y * h))
            
            return coordinate
    
    timesStationary = 0
    coordinateField = []
    
    #distance between two tuples
    def dist(self, pos1, pos2):
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return np.sqrt(np.power(dx, 2) + np.power(dy, 2))
    
    prevCoords = []
    def addNewCoordinate(self, coordinate, dt):
        if coordinate == None: return
        
        if len(self.prevCoords) >= 2:
            xmean = sum([a[0] for a in self.prevCoords]) / len(self.prevCoords)
            ymean = sum([a[1] for a in self.prevCoords]) / len(self.prevCoords)
            
            newCoord = (xmean, ymean)
            
            self.coordinateField.append(newCoord)
            self.prevCoords.clear()
            
        else:
            self.prevCoords.append(coordinate)
    
    #renders the coordinates, drawing lines between each
    def render(self, frame, colorDisplay):
        
        arr = np.array(self.coordinateField)
        cv2.polylines(frame, np.int32([arr]), False, colorDisplay.getColor(), 2)
    
    #updates the coordinate field with the last index position;
    #returns and clears coordinate field when finished;
    #coordinate field is finished when the finger is less than [minThreshold] pixels of the start of the shape;
    def update(self, frame, idleThreshold, dt, colorDisplay):
        pos = self.getIndexPosition(frame)
        self.render(frame, colorDisplay)
        
        color = colorDisplay.getColor()
        
        if keyboard.is_pressed('a'): self.addNewCoordinate(pos, dt)
        
        if len(self.coordinateField) == 0 or pos == None: return
            
        if len(self.coordinateField) >= 2:
            prevPos = self.coordinateField[-2]
            dx = pos[0] - prevPos[0]
            dy = pos[1] - prevPos[1]
            dist = np.sqrt(np.power(dx, 2) + np.power(dy, 2))
            
            if dist < idleThreshold:
                self.timesStationary += 1
        
        dist = self.dist(self.coordinateField[0], pos)
        if not keyboard.is_pressed('a') and len(self.coordinateField) > 0:
            colorDisplay.newLineList([self.coordinateField.copy(), color])
            self.coordinateField.clear()
            self.prevCoords.clear()
        
class ColorDisplay:
    lineBuffer = []
    
    def getColor(self):
        return self.colors[self.colorIndex]
    
    def newLineList(self, lineList):
        self.lineBuffer.append(lineList)
        print("new line")
    
    colorPickerOn = True
    sDown = False
    def render(self, frame):
        #LINES!!!!
        if keyboard.is_pressed("x"): self.lineBuffer.clear()
        if keyboard.is_pressed("s"):
            if self.sDown == False: self.colorPickerOn = not self.colorPickerOn
            self.sDown = True
        else: self.sDown = False
            
        for lineList in self.lineBuffer:
            arr = np.array(lineList[0])
            cv2.polylines(frame, np.int32([arr]), False, lineList[1], 2)
            
        #COLOR PICKER!!!
        if (not self.colorPickerOn): return
        cv2.rectangle(frame, (0,0), (50, 50), self.colors[self.colorIndex], -1)
    
    colorIndex = 0
    colors = [
        (0, 0, 255),
        (20, 112, 237),
        (0, 255, 255),
        (0, 255, 0),
        (255, 0, 0),
        (255, 0, 127),
        (0, 0, 0),
        (255,255,255)
    ]
    def incrementColorPicker(self):
        if not self.colorPickerOn: return
        
        self.colorIndex+=1
        if (self.colorIndex >= len(self.colors)):
            self.colorIndex = 0
        
def main():    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    detector = handTracker()
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    dt = 0
    colorDisp = ColorDisplay()
    zDown = False
    with pyvirtualcam.Camera(width=1280, height=720, fps=60,fmt=pyvirtualcam.PixelFormat.BGR) as cam:
        while True:
            startTime = time.time()
            
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
                
            detector.update(frame, 10, dt, colorDisp)
            if keyboard.is_pressed("z"):
                if zDown == False: colorDisp.incrementColorPicker()
                zDown = True
            else: zDown = False
            
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            colorDisp.render(frame)
            
            cam.send(frame)
            cam.sleep_until_next_frame()
            
            dt = time.time() - startTime
            
if __name__ == "__main__":
    main()