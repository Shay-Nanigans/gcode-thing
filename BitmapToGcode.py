#draws a fuckton of tiny lines and pretends its an arc.

import os
import math
from PIL import Image

filePath=os.path.dirname(os.path.realpath(__file__))

#directory settings
dirIn = filePath+"/imgin"
dirOut = filePath+"/gcodeout"
dirProc = filePath+"/gcodeprocessed"
print(dirIn)

#printer settings (in mm)
# printerWidth=200    
# printerHeight=200
imgDetail=0.1 #how fine to slice. in mm

#pen X Y Z. These should probably be negative
offsetX=-50
offsetY=-30
offsetZ=-10 #pen dropped touching the plate

#pen heights
liftedZ=1   #number of millimeters pen gets lifted above the plate
blackZ= 0    #number of millimeters pen gets pushed into the plate when drawing black

#image settings
trueBlack=50 #everything equal or lower than this is black
trueWhite=200 #everything equal or higher is white

imgMaxSizeX=200 #max x size of image
imgMaxSizeY=200 #max y size of image


def arrayPrint(arr):
    print("----------------------------------------")
    for y in arr:
        strArr=""
        for  x in y:
            strArr = strArr + str(x) + " "
        print(strArr)
        

def initialG():
    gcodeStr=[]
    gcodeStr.append("G21")
    gcodeStr.append("G1 F7200")
    gcodeStr.append("G91")
    gcodeStr.append("Z"+str(liftedZ*2))
    gcodeStr.append("G90")
    gcodeStr.append("M206 X" + str(offsetX) +" Y"+str(offsetY)+" Z"+str(offsetZ) )
    gcodeStr.append("G28")
    gcodeStr.append("G1 Z"+str(liftedZ))
    gcodeStr.append("G1 Y0")
    gcodeStr.append("G1 X0")
    return gcodeStr

#changes file to an 2D array of grayscale pixels
def toPixelArray(fileName):
    img = Image.open(dirIn+"/"+fileName)
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
def findSpiral(imgArrBlack, gcodeStr, col, row):
    lastPosition=4 # where X is center
    # 5 6 7 
    # 4 X 0
    # 3 2 1
    cardinalDir=[[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]


    gcodeStr.append("G0 Z"+str(liftedZ))
    gcodeStr.append("G0 X"+str(col*imgDetail)+" Y"+str(row*imgDetail))
    gcodeStr.append("G0 Z"+str(-blackZ))
    imgArrBlack[row][col]=False

    
    posCheck=5
    appended=0
    while posCheck!=lastPosition:
        if(row+cardinalDir[posCheck][0]>=0 and col+cardinalDir[posCheck][1]>=0 and row+cardinalDir[posCheck][0]<len(imgArrBlack) and col+cardinalDir[posCheck][1]<len(imgArrBlack[0])):
            if(imgArrBlack[row+cardinalDir[posCheck][0]][col+cardinalDir[posCheck][1]]):
                row=row+cardinalDir[posCheck][0]
                col=col+cardinalDir[posCheck][1]
                gcodeStr.append("G0 X"+str(col*imgDetail)+" Y"+str(row*imgDetail))
                imgArrBlack[row][col]=False
                posCheck=posCheck+4
                appended=appended+1
        posCheck=posCheck+1
        if posCheck>7: posCheck=posCheck-8
        
    gcodeStr.append("G0 Z"+str(liftedZ))
    print("Appended: "+str(appended))
    return gcodeStr


def spiralGCode(imgArrBlack, gcodeStr):
    row = 0
    col = 0
    print(str(len(imgArrBlack))+" "+str(len(imgArrBlack[0])))
    while(row<len(imgArrBlack)):
        # print(imgArrBlack[row])
        col=0
        while(col<len(imgArrBlack[row])):
            if(imgArrBlack[row][col]==True):
                gcodeStr=findSpiral(imgArrBlack,gcodeStr,col,row)

            col=col+1
        row=row+1
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
    # print(len(imgArr2))
    # print(len(imgArr2[0]))
    # arrayPrint(imgArr2)
    # print("---------------------------")
    # print(len(imgArrBlack))
    # print(len(imgArrBlack[0]))
    # arrayPrint(imgArrBlack)
    # print("---------------------------")
    # print(len(imgArrGrey))
    # print(len(imgArrGrey[0]))
    # arrayPrint(imgArrGrey)
    arrayPrint(imgArrBlack)
    gcodeStr= initialG()
    gcodeStr=spiralGCode(imgArrBlack, gcodeStr)

    return gcodeStr

def writeFile(newFile,gcodeStr):
    for line in gcodeStr:
        newFile.write(line+"\n")
    newFile.close()

#MAIN METHOD
for root, dirs, files in os.walk(dirIn):
    for fileName in files:

        gcodeStr=convert(fileName)
        writeFile((open(dirOut+"/"+fileName+".gcode","w")),gcodeStr)
        #os.rename(dirIn+"/"+fileName, dirProc+"/"+fileName)



