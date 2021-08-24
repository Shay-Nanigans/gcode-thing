#draws a fuckton of tiny lines and pretends its an arc.

from ntpath import join
import os
import math
from PIL import Image
import json



filePath=os.path.dirname(os.path.realpath(__file__))
settings = json.load(open(filePath+"/config.json"))

#directory settings
dirImgIn = filePath+"/"+str(settings["file"]["dirInImg"])    
dirOut = filePath+"/"+str(settings["file"]["dirOut"]) 
dirProc = filePath+"/"+str(settings["file"]["dirProc"])

#printer settings (in mm)
imgDetail= settings["printerSettings"]["imgDetail"]#how fine to slice. in mm

#pen X Y Z. These should probably be negative
offsetX=0-settings["printerSettings"]["offsetXYZ"][0]
offsetY=0-settings["printerSettings"]["offsetXYZ"][1]
offsetZ=0-settings["printerSettings"]["offsetXYZ"][2] #pen dropped touching the plate

#pen heights
liftedZ=settings["printerSettings"]["penHeights"]["liftedZ"]   #number of millimeters pen gets lifted above the plate
blackZ= settings["printerSettings"]["penHeights"]["blackZ"]     #number of millimeters pen gets lifted above the plate when drawing black
greyDarkZ = settings["printerSettings"]["penHeights"]["greyDarkZ"]  #darkest grey   (1/255)
greyLightZ = settings["printerSettings"]["penHeights"]["greyLightZ"]  #lightest grey (254/255) This should be higher than greyDarkZ

#image settings
trueBlack=settings["imageSettings"]["trueBlack"] #everything equal or lower than this is black
trueWhite=settings["imageSettings"]["trueWhite"] #everything equal or higher is white

minAppend=settings["imageSettings"]["minAppend"]

imgMaxSizeX=settings["printerSettings"]["imgMaxSize"][0] #max x size of image
imgMaxSizeY=settings["printerSettings"]["imgMaxSize"][1] #max y size of image


def arrayPrint(arr):
    print("----------------------------------------")
    for y in arr:
        strArr=""
        for  x in y:
            strArr = strArr + str(x) + " "
        print(strArr)
        
#initial Gcode at the start of the gcode file.
def initialG():
    gcodeStr=[]
    gcodeStr.append("G21")
    gcodeStr.append("G1 F7200")
    gcodeStr.append("G91")
    gcodeStr.append("G1 Z"+str(liftedZ*2))
    gcodeStr.append("G90")
    gcodeStr.append("M206 X" + str(offsetX) +" Y"+str(offsetY)+" Z"+str(offsetZ) )
    gcodeStr.append("G28")
    gcodeStr.append("G1 Z"+str(liftedZ))
    gcodeStr.append("G1 Y0")
    gcodeStr.append("G1 X0")
    return gcodeStr

def finalStage(gcodeStr):
    gcodeStr.append("G1 Z"+str(liftedZ*2))
    gcodeStr.append("G1 X0 Y0")
    gcodeStr.append("M206 X0 Y0 Z0" )
    return gcodeStr

#changes file to an 2D array of grayscale pixels
def toPixelArray(fileName):
    img = Image.open(dirImgIn+"/"+fileName)
    px=img.load()
    print(img)
    imgArr = []
    for row in range(0,img.height):
        rowLst=[]
        for col in reversed(range(0,img.width)):
            dot=px[col,row]
            rowLst.append(int((dot[0]+dot[1]+dot[2])/3))
        imgArr.append(rowLst)
    img.close()
    return imgArr

#updates img so any pixel below a threshold is black or above is white
def whiteoutBlackout(imgArr):
    for row in range(0,len(imgArr)):
        for col in range(0,len(imgArr[row])):
            if imgArr[row][col] < trueBlack:
                imgArr[row][col]=0
            elif imgArr[row][col] > trueWhite:
                imgArr[row][col]=255
    return imgArr

#splits image into a 2D boolean array of black pixels and a 2D array of grayscale pixels

def printerPixel(imgArr):
    xRes=int(imgMaxSizeX/imgDetail)
    yRes=int(imgMaxSizeY/imgDetail)
    newArr=[]
    for y in range(0,yRes):
        rowLst=[]
        for x in range(0,xRes):
            rowLst.append(255)
        newArr.append(rowLst)
    
    #determine constraint
    if(xRes/len(imgArr[0])==(yRes/len(imgArr))):
        pixelsPerImgPixel=len(imgArr)/xRes
    elif(xRes/len(imgArr[0])<(yRes/len(imgArr))):
        pixelsPerImgPixel=len(imgArr[0])/xRes
    else:
        pixelsPerImgPixel=len(imgArr)/yRes

    # print(len(newArr))
    # print(len(newArr[0]))
    print(pixelsPerImgPixel)
    for y in range(0,yRes):
        for x in range(0,xRes):
            try:
                newArr[x][y]=imgArr[int(pixelsPerImgPixel*x)][int(pixelsPerImgPixel*y)]
            except:
                pass
            
    return newArr

    #finds a spiral with the classic old maze turn left algorithm
def findSpiral(imgArrBlack, gcodeStr, col, row):
    lastPosition=6 # where X is center
    # 5 6 7 
    # 4 X 0
    # 3 2 1
    cardinalDir=[[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]

    gcodeAddStr=[]

    gcodeAddStr.append([row, col])
    # gcodeAddStr.append("G0 Z"+str(liftedZ))
    # gcodeAddStr.append("G0 X"+str(col*imgDetail)+" Y"+str(row*imgDetail))
    # gcodeAddStr.append("G0 Z"+str(blackZ))
    imgArrBlack[row][col]=False

    
    posCheck=lastPosition+1
    if posCheck>7: posCheck=posCheck-8
    appended=0
    while posCheck!=lastPosition:
        if(row+cardinalDir[posCheck][0]>=0 and col+cardinalDir[posCheck][1]>=0 and row+cardinalDir[posCheck][0]<len(imgArrBlack) and col+cardinalDir[posCheck][1]<len(imgArrBlack[0])):
            if(imgArrBlack[row+cardinalDir[posCheck][0]][col+cardinalDir[posCheck][1]]):
                row=row+cardinalDir[posCheck][0]
                col=col+cardinalDir[posCheck][1]
                gcodeAddStr.append([row, col])
                imgArrBlack[row][col]=False
                posCheck=posCheck+4
                lastPosition=posCheck
                if lastPosition>7: lastPosition=lastPosition-8
                appended=appended+1
                # if appended%100==0 and appended>0:
                #     print(appended)
                    
        posCheck=posCheck+1
        if posCheck>7: posCheck=posCheck-8
        
    # gcodeAddStr.append("G0 Z"+str(liftedZ))
    # print("Appended: "+str(appended))
    # if appended>=minAppend:
    #     for line in gcodeAddStr:
    #         gcodeStr.append(line)
    return gcodeAddStr


#nightmarish code to rebuild the spiral list 
def addSpiral(spirals, newSpiral):
    newSpirals=[]
    joinedFlag = False
    #print(newSpiral)
    for spiral in spirals: #checks the new spiral against every old one.
        if(joinedFlag):
            newSpirals.append(spiral)
        elif newSpiral==None:
            newSpirals.append(spiral)
        elif not spiral==None:
            
            #checks if the spiral is a dot, and tries to add it to the side of another 
            if len(spiral)==1:
                i=0
                while (i<len(newSpiral)) and not joinedFlag:
                    if abs(newSpiral[i][0]-spiral[0][0]) <= 1 and abs(newSpiral[i][1]-spiral[0][1]) <= 1:
                        newSpiral.insert(i,spiral[0])
                        joinedFlag = True
                    i=i+1

            #checks if start of new spiral is beside end of the old spiral
            elif abs(newSpiral[0][0]-spiral[len(spiral)-1][0])<=1 and abs(newSpiral[0][1]-spiral[len(spiral)-1][1])<=1:
                newSpiral = spiral + newSpiral
                joinedFlag = True
            #checks end of the new spiral against the beginning of the old one
            elif abs(newSpiral[len(newSpiral)-1][0]-spiral[0][0])<=1 and abs(newSpiral[len(newSpiral)-1][1]-spiral[0][1])<=1:
                newSpiral = newSpiral + spiral
                joinedFlag = True
            #start to start
            elif abs(newSpiral[0][0]-spiral[0][0])<=1 and abs(newSpiral[0][1]-spiral[0][1])<=1:
                newSpiral = list(reversed(spiral)) + newSpiral
                joinedFlag = True
            #end to end
            elif abs(newSpiral[len(newSpiral)-1][0]-spiral[len(spiral)-1][0])<=1 and abs(newSpiral[len(newSpiral)-1][1]-spiral[len(spiral)-1][1])<=1:
                newSpiral = spiral + list(reversed(newSpiral))
                joinedFlag = True

            else:
                #dont mind the madness as it tried to join the middle of things
                i=0
                while (i<len(newSpiral)-1) and not joinedFlag:

                    #checks if the beginning of a spiral and the end of a spiral can be put in between two spots
                    if abs(newSpiral[i][0]-spiral[0][0])<=1 and abs(newSpiral[i][1]-spiral[0][1])<=1 and abs(newSpiral[i+1][0]-spiral[len(spiral)-1][0])<=1 and abs(newSpiral[i+1][1]-spiral[len(spiral)-1][1])<=1:
                        newSpiral[i:i]=spiral
                        joinedFlag = True
                    #same but backwards
                    elif abs(newSpiral[i+1][0]-spiral[0][0])<=1 and abs(newSpiral[i+1][1]-spiral[0][1])<=1 and abs(newSpiral[i][0]-spiral[len(spiral)-1][0])<=1 and abs(newSpiral[i][1]-spiral[len(spiral)-1][1])<=1:
                        newSpiral[i:i]=list(reversed(spiral))
                        joinedFlag = True
                    
                    
                    i=i+1

                i=0
                while (i<len(spiral)-1) and not joinedFlag:

                    #checks if the beginning of a spiral and the end of a spiral can be put in between two spots
                    if abs(newSpiral[0][0]-spiral[i][0])<=1 and abs(newSpiral[0][1]-spiral[i][1])<=1 and abs(newSpiral[len(newSpiral)-1][0]-spiral[i+1][0])<=1 and abs(newSpiral[len(newSpiral)-1][1]-spiral[i+1][1])<=1:
                        spiral[i:i]=newSpiral
                        newSpiral=spiral
                        joinedFlag = True
                    #same but backwards
                    elif abs(newSpiral[0][0]-spiral[i+1][0])<=1 and abs(newSpiral[0][1]-spiral[i+1][1])<=1 and abs(newSpiral[len(newSpiral)-1][0]-spiral[i][0])<=1 and abs(newSpiral[len(newSpiral)-1][1]-spiral[i][1])<=1:
                        spiral[i:i]=list(reversed(newSpiral))
                        newSpiral=spiral
                        joinedFlag = True
                    
                    
                    i=i+1
            if not joinedFlag:
                newSpirals.append(spiral)


    print(len(newSpirals))
    if(joinedFlag):
        newSpirals = addSpiral(newSpirals, newSpiral)
    else:
        newSpirals.append(newSpiral)
    
    return newSpirals


def findClosestStart(row,col,spirals):
    closeDistance=(imgMaxSizeX+imgMaxSizeY)/imgDetail
    closest=0 , True
    i=0
    while i<len(spirals):
        dist=math.sqrt((row-spirals[i][0][0])**2 + (col-spirals[i][0][1])**2)
        if dist<closeDistance:
            closeDistance = dist
            closest = i , True
        dist=math.sqrt((row-spirals[i][len(spirals[i])-1][0])**2 + (col-spirals[i][len(spirals[i])-1][1])**2)
        if dist<closeDistance:
            closeDistance = dist
            closest = i , False
        i=i+1
    if closest[1]:
        closest=spirals.pop(closest[0])
        return closest, spirals
    else: 
        closest=spirals.pop(closest[0])
        return list(reversed(closest)), spirals

#finds all the spirals needed for the code.
#horribly ineffecient and bruteforcy, but a second on the cpu saves an hour on the printer
def spiralGCode(imgArrBlack, gcodeStr):
    row = 0
    col = 0
    print("Size: "+ str(len(imgArrBlack))+" "+str(len(imgArrBlack[0])))
    spirals=[]
    while(row<len(imgArrBlack)):
        # print(imgArrBlack[row])
        # if row%2 == 0:
        col=0
        while(col<len(imgArrBlack[row])):
            if(imgArrBlack[row][col]==True):
                spirals.append(findSpiral(imgArrBlack,gcodeStr,col,row))
                
            col=col+1
        # else:
        #     col=len(imgArrBlack[row])-1
        #     while(col>0):
        #         if(imgArrBlack[row][col]==True):
        #             gcodeStr=findSpiral(imgArrBlack,gcodeStr,col,row)

        #         col=col-1

        row=row+1
    spirals.sort(key=len)
    originalSpirals = len(spirals)

    #conbines any ajacent spirals
    newSpirals=[]
    for spiral in spirals:
        print("len: "+str(len(spiral)))
        newSpirals=addSpiral(newSpirals, spiral)
    spirals = newSpirals

    #drops any small spirals
    newSpirals=[]
    tooSmall = 0
    for spiral in reversed(spirals):
        if(len(spiral) < minAppend):
            tooSmall=tooSmall+1
        else:
            newSpirals.append(spiral)
    spirals = newSpirals

    #orders them so the distance of the ends are as close together as possible
    newSpirals=[]
    spiral=spirals.pop(0)
    newSpirals.append(spiral)
    while len(spirals)>0:
        row=spiral[len(spiral)-1][0]
        col=spiral[len(spiral)-1][1]
        spiral,spirals = findClosestStart(row, col,spirals)
        newSpirals.append(spiral)
    spirals=newSpirals



    spiralLen=["Dots in spiral: "]
    for spiral in spirals:
        gcodeStr.append("G0 Z"+str(liftedZ))
        gcodeStr.append("G0 X"+str(spiral[0][1]*imgDetail)+" Y"+str(spiral[0][0]*imgDetail))
        gcodeStr.append("G0 Z"+str(blackZ))
        spiralLen.append(len(spiral))
        for dot in spiral:
            gcodeStr.append("G0 X"+str(dot[1]*imgDetail)+" Y"+str(dot[0]*imgDetail))
    print(spiralLen)
    print("total spirals made: " + str(originalSpirals))
    print("Small spirals dropped: "+str(tooSmall))
    print("total spirals added: " + str(len(spirals)))
    gcodeStr.append("G0 Z"+str(liftedZ))
    return gcodeStr

def zigZagGrey(imgArrGrey,imgArrBlack, gcodeStr):
    lastWhite=False
    for row in range(0, len(imgArrGrey)):
        if not lastWhite:
            gcodeStr.append("G0 Z"+str(liftedZ))
            lastWhite=True
        for col in range(0,len(imgArrGrey[row])):
            if not imgArrBlack[row][col]:
                if imgArrGrey[row][col]==255:
                    if not lastWhite:
                        gcodeStr.append("G0 Z"+str(liftedZ))
                else:
                    if lastWhite:
                        gcodeStr.append("G0 X" + str(col*imgDetail)+" Y"+ str(row*imgDetail))
                        gcodeStr.append("G0 Z" + str(greyDarkZ+(greyLightZ-greyDarkZ)*(float(imgArrGrey[row][col])/255)))
                    else:
                        gcodeStr.append("G0 X" + str(col*imgDetail)+" Y"+ str(row*imgDetail) +" Z" + str(greyDarkZ+(greyLightZ-greyDarkZ)*(float(imgArrGrey[row][col])/255)))
                lastWhite = imgArrGrey[row][col]==255
    gcodeStr.append("G0 Z"+str(liftedZ))
    return gcodeStr


def splitBlack(imgArr):
    imgArrBlack=[]
    imgArrGrey=[]
    for row in imgArr:
        rowBlack=[]
        rowGrey=[]
        for col in row:
            if col == 0:
                rowBlack.append(True)
                rowGrey.append(255)
            else:
                rowBlack.append(False)
                rowGrey.append(col)
        imgArrBlack.append(rowBlack)
        imgArrGrey.append(rowGrey)
    return imgArrBlack, imgArrGrey


def convert(fileName):
    print(fileName)
    imgArr = toPixelArray(fileName)
    imgArr = whiteoutBlackout(imgArr)
    imgArr2 = printerPixel(imgArr)
    imgArrBlack, imgArrGrey = splitBlack(imgArr2)
    #arrayPrint(imgArrBlack)
    gcodeStr= initialG()
    gcodeStr=spiralGCode(imgArrBlack, gcodeStr)
    gcodeStr= zigZagGrey(imgArrGrey, imgArrBlack ,gcodeStr)
    gcodeStr=finalStage(gcodeStr)
    return gcodeStr

def writeFile(newFile,gcodeStr):
    for line in gcodeStr:
        newFile.write(line+"\n")
    newFile.close()

#MAIN METHOD
for root, dirs, files in os.walk(dirImgIn):
    for fileName in files:

        gcodeStr=convert(fileName)
        writeFile((open(dirOut+"/"+fileName+".gcode","w")),gcodeStr)
        #os.rename(dirIn+"/"+fileName, dirProc+"/"+fileName)



