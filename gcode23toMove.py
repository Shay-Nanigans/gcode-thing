# Changes any simple G2 or G3 arcs into straight moves to the final destination

import os

dirIn = "H:/Bots/gcode thing/gcodein"
dirOut = "H:/Bots/gcode thing/gcodeout"
dirProc = "H:/Bots/gcode thing/gcodeprocessed"



def convert(fileName):
    print(fileName)
    file=open(dirIn+"/"+fileName)
    newFile = open(dirOut+"/"+fileName,"w")
    for line in file:
        try:
            if((line[1]=="2" or line[1]=="3") and line[0]=="G" and line[2]==" "):
                line = line[:1] + "1" + line[1 + 1:]
                newFile.write("G0 Z1 \n")
                newFile.write(line)
                newFile.write("G0 Z0 \n")
                newFile.write("")
            else:
                newFile.write(line)
        except Exception as e:
            newFile.write(line)
            # print("except: " + str(e))

    newFile.close()
    file.close()







for root, dirs, files in os.walk(dirIn):
    for fileName in files:

        convert(fileName)
        os.rename(dirIn+"/"+fileName, dirProc+"/"+fileName)

