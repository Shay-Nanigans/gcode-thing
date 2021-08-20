#draws a fuckton of tiny lines and pretends its an arc.

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

    print(len(newArr))
    print(len(newArr[0]))
    print(pixelsPerImgPixel)
    for y in range(0,yRes):
        for x in range(0,xRes):
            try:
                newArr[x][y]=imgArr[int(pixelsPerImgPixel*x)][int(pixelsPerImgPixel*y)]
            except:
                pass
            
    return newArr

    #finds a spiral with 
def findSpiral(imgArrBlack, gcodeStr, col, row):
    lastPosition=6 # where X is center
    # 5 6 7 
    # 4 X 0
    # 3 2 1
    cardinalDir=[[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]

    gcodeAddStr=[]

    gcodeAddStr.append("G0 Z"+str(liftedZ))
    gcodeAddStr.append("G0 X"+str(col*imgDetail)+" Y"+str(row*imgDetail))
    gcodeAddStr.append("G0 Z"+str(blackZ))
    imgArrBlack[row][col]=False

    
    posCheck=lastPosition+1
    if posCheck>7: posCheck=posCheck-8
    appended=0
    while posCheck!=lastPosition:
        if(row+cardinalDir[posCheck][0]>=0 and col+cardinalDir[posCheck][1]>=0 and row+cardinalDir[posCheck][0]<len(imgArrBlack) and col+cardinalDir[posCheck][1]<len(imgArrBlack[0])):
            if(imgArrBlack[row+cardinalDir[posCheck][0]][col+cardinalDir[posCheck][1]]):
                row=row+cardinalDir[posCheck][0]
                col=col+cardinalDir[posCheck][1]
                gcodeAddStr.append("G0 X"+str(col*imgDetail)+" Y"+str(row*imgDetail))
                imgArrBlack[row][col]=False
                posCheck=posCheck+4
                lastPosition=posCheck
                if lastPosition>7: lastPosition=lastPosition-8
                appended=appended+1
        posCheck=posCheck+1
        if posCheck>7: posCheck=posCheck-8
        if appended%100==0 and appended>0:
            print(appended)
        
    gcodeAddStr.append("G0 Z"+str(liftedZ))
    print("Appended: "+str(appended))
    if appended>=minAppend:
        for line in gcodeAddStr:
            gcodeStr.append(line)
    return gcodeStr


def spiralGCode(imgArrBlack, gcodeStr):
    row = 0
    col = 0
    print(str(len(imgArrBlack))+" "+str(len(imgArrBlack[0])))
    while(row<len(imgArrBlack)):
        # print(imgArrBlack[row])
        # if row%2 == 0:
        col=0
        while(col<len(imgArrBlack[row])):
            if(imgArrBlack[row][col]==True):
                gcodeStr=findSpiral(imgArrBlack,gcodeStr,col,row)
            col=col+1
        # else:
        #     col=len(imgArrBlack[row])-1
        #     while(col>0):
        #         if(imgArrBlack[row][col]==True):
        #             gcodeStr=findSpiral(imgArrBlack,gcodeStr,col,row)

        #         col=col-1

        row=row+1
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
    imgArr = toPixelArray(fileName)
    imgArr = whiteoutBlackout(imgArr)
    imgArr2 = printerPixel(imgArr)
    imgArrBlack, imgArrGrey = splitBlack(imgArr2)
    arrayPrint(imgArrBlack)
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



