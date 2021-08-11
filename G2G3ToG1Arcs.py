#draws a fuckton of tiny lines and pretends its an arc.

import os
import math

dirIn = "H:/Bots/gcode thing/gcodein"
dirOut = "H:/Bots/gcode thing/gcodeout"
dirProc = "H:/Bots/gcode thing/gcodeprocessed"

arcLineSize=0.5 #line length. in units? probably millimeters

#breaks lines into their component commands and returns a dictionary
def shatterLine(line):
    cmdStr = line.split(" ")
    cmdArr={}
    for cmd in cmdStr:
        try:
            if(cmd[0]=="G"):
                cmdArr[cmd[0]]={"key":cmd[0], "val":int(cmd[1:])}
            else:
                cmdArr[cmd[0]]={"key":cmd[0], "val":float(cmd[1:])}
        except Exception as e:
            print(e)
            print(cmd + " thrown out")
    return cmdArr

#takes a curved line and returns an array of tiny straight lines
def IJtoLines(lastX, lastY, lineCommands):
    centerX=lastX+lineCommands["I"]["val"]
    centerY=lastY+lineCommands["J"]["val"]
    
    beforeR=math.sqrt((lastX-centerX)**2+(lastY-centerY)**2)
    afterR=math.sqrt((lineCommands["X"]["val"]-centerX)**2+(lineCommands["Y"]["val"]-centerY)**2)

    radStart= math.atan2(lastY-centerY,lastX-centerX)
    radEnd= math.atan2(lineCommands["Y"]["val"]-centerY,lineCommands["X"]["val"]-centerX)
    
    if radStart<0:
        radStart=radStart+(2*math.pi)
    if radEnd<0:
        radEnd=radEnd+(2*math.pi)

    direction = 1
    #g2 is clockwise (decreasing radians) and g3 is counterclockwise (increasing radians)
    if(lineCommands["G"]["val"]==2):
        if radStart<radEnd:                 #clockwise goes down so start has to be bigger
            radStart=radStart+(2*math.pi)
        direction = -1
    elif(lineCommands["G"]["val"]==3):
        if radStart>radEnd:                 #counter clockwise goes up so end has to be bigger
            radEnd=radEnd+(2*math.pi)

    stepSize=direction/(((beforeR+afterR)/2)/arcLineSize)

    angle=radStart
    roundLines=[]
    while direction*angle < direction*radEnd:
        angle=angle+stepSize
        newLine = lineCommands.copy()
        newLine.pop("I")
        newLine.pop("J")
        newLine["X"]["val"]= afterR * math.cos(angle) + centerX
        newLine["Y"]["val"]= afterR * math.sin(angle) + centerY
        newLine["G"]["val"]= 1
        
        roundLines.append(newLine)

    return roundLines






    

#writes line dict to file
def writeLine(newFile,line):
    lineStr=""
    for key in line:
        lineStr=lineStr+key+str(line[key]["val"])+" "
    newFile.write(lineStr+"\n")

#converts given file
def convert(fileName):
    print(fileName)
    file=open(dirIn+"/"+fileName)
    newFile = open(dirOut+"/"+fileName,"w")
    lastX=0
    lastY=0
    for line in file:
        # try:
            lineCommands=shatterLine(line)

            if("G" in lineCommands):
                if(lineCommands["G"]["val"]==2 or lineCommands["G"]["val"]==3):
                    lineArr = IJtoLines(lastX, lastY, lineCommands)
                    for lineLine in lineArr:
                        writeLine(newFile, lineLine)
                else:
                    writeLine(newFile, lineCommands)
            else:
                writeLine(newFile, lineCommands)
            if("X" in lineCommands):
                lastX=lineCommands["X"]["val"]
            if("Y" in lineCommands):
                lastY=lineCommands["Y"]["val"]
            
        # except Exception as e:
        #     print("stubborn line: "+ str(line))
            # print(str(e))
    newFile.close()
    file.close()






#public static void main(String args[])
for root, dirs, files in os.walk(dirIn):
    for fileName in files:

        convert(fileName)
        os.rename(dirIn+"/"+fileName, dirProc+"/"+fileName)

