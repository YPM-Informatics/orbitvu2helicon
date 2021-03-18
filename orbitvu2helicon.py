import os
from shutil import copyfile, move
import subprocess
import tkinter as tk
import math
from tkinter import filedialog
import collections
from PIL import Image
import json



def scanFolder(dir):
    inputDir = os.path.normpath(dir)
    outputDir = inputDir.rstrip("\\") + "-arc"
    sessionFile = "session.json"
    totalPositions = 0
    stackFolders = []
    rows = {}
    stackDepthsByRow = {}
    errors = []
    cmds = []
	
	
    #scan directory and build dictionary of rows and positions for each row
    if os.path.exists(inputDir):
        d = os.listdir(inputDir)
        counter = 0
        for s in d:
            if os.path.isfile(os.path.join(inputDir, s)) and s.lower().startswith('360_') and s.lower().endswith('.jpg') and os.path.isdir(os.path.join(outputDir, s[:-4])) == False:
                temp = s[:-4].split('_')
                if len(temp) == 3:
                    totalPositions = totalPositions +1;
                    row = int(temp[1])
                    position = int(temp[2])
                    if row in rows:
                        rows[row].append(position)
                    else:
                        rows[row] = [position]
    
    print("Orbitvu does not control me!")
    print("***********************************")
    print(totalPositions, " images discovered for processing")
    print(len(rows), " rows discovered for processing")
    print("***********************************")
    for row, positions in rows.items():
        stackDepth = int(input("Enter Stack Depth for row " + str(row) + " (" + str(len(positions)) + " images):"))
        while len(positions)%stackDepth != 0:
            print("Invalid stack depth given number of images in row. Try again, crtl-C to exit.")
            stackDepthsByRow = int(input("Enter Stack Depth for row " + str(row) + " (" + str(len(positions)) + " images):"))
        stackDepthsByRow[row] = stackDepth
    print("***********************************")

	
    #DryRun PreValidation:
    #make sure position are sorted so filelists can be created in correct order later on
    #also make sure the number of positions per row is valid for the given stack depth
    #finally ensure all files exist before starting move process
    for row, positions in rows.items():
        positions.sort()
        if len(positions)%stackDepthsByRow[row] != 0:
            errors.append('Inavalid number of files detected in row:' + str(row) + ' to generate stack depth of ' + str(stackDepthsByRow[row]) )
        else:
            numStacks = len(positions)//stackDepthsByRow[row]
            for x in range(0,numStacks): 
                for p in range(0,stackDepthsByRow[row]):
                    f_pos = positions[p*numStacks+x]
                    filename = '_'.join(['360','{:02d}'.format(row), '{:05d}'.format(f_pos)]) + '.jpg'
                    if os.path.exists(os.path.join(inputDir,filename)) == False:
                        errors.append("File Error: " + os.path.join(inputDir,filename))
    if len(errors) > 0:
        raise ValueError('\n'.join(errors))
    


    #Move all files and create file lists
    for row, positions in rows.items():
        numStacks = len(positions)//stackDepthsByRow[row]
        for x in range(0,numStacks): 
            stackFolder = '_'.join(['360','{:02d}'.format(row), '{:05d}'.format(x + 1) ])
            os.makedirs(os.path.join(outputDir,stackFolder), exist_ok=True)
            print("creating:",os.path.join(outputDir,stackFolder))
            for p in range(0,stackDepthsByRow[row]): 
                i = p*numStacks+x
                f_pos = positions[p*numStacks+x]
                filename = '_'.join(['360','{:02d}'.format(row), '{:05d}'.format(f_pos)]) + '.jpg' 
                move(os.path.join(inputDir,filename), os.path.join(outputDir,stackFolder,filename))
                print("moving:",filename)
                f=open(os.path.join(outputDir, stackFolder, 'stacklist.txt'),"at")
                f.write(os.path.join(outputDir,stackFolder, filename) + '\n')
                f.close()
            inputStackList = os.path.join(outputDir, stackFolder, 'stacklist.txt')
            saveArg = "-save:" + os.path.join(outputDir, stackFolder + ".tif")
            cmd = ['heliconfocus.exe', "-rp:8", "-sp:4", "-mp:1", "-va:3", "-ha:3", "-ra:0", "-ma:5", "-dmf:3", "-im:1", "-ba:1", "-i", inputStackList, saveArg, "-silent" ]
            cmds.append(cmd) 

    for cmd in cmds:
        print('executing:', ' '.join(cmd))
        subprocess.call(cmd)

    #convert outputTifs to JPGs
    for row, positions in rows.items():
        numStacks = len(positions)//stackDepthsByRow[row]
        for x in range(0,numStacks): 
            inputTif = os.path.join(outputDir, '_'.join(['360','{:02d}'.format(row), '{:05d}'.format(x + 1) ]) + ".tif")
            outputJPG = os.path.join(inputDir, '_'.join(['360','{:02d}'.format(row), '{:05d}'.format(x + 1) ]) + ".jpg")
            if os.path.exists(inputTif) and  not os.path.exists(outputJPG):
                print('converting:',inputTif)
                with Image.open(inputTif) as image:
                    image.save(outputJPG, optimize=True, quality=97)
            else:
               print('skipping:', inputTif) 
    
	
	#prepare spoofed session json data to match 3d files in project directory
    if os.path.exists(inputDir) and os.path.exists(os.path.join(inputDir, sessionFile)):
        print('adjusting session file')
        sessionData = None
        d = os.listdir(inputDir)
        with open(os.path.join(inputDir,sessionFile), 'rt', encoding='utf8') as f:
                sessionData = json.loads(f.read())
                f.close()
        images_360 = []
        for image_360 in sessionData["images_360"]:
            if "filename" in image_360["main"]:
                if image_360["main"]["filename"] in d:
                     images_360.append(image_360)
                     print(image_360["main"]["filename"])
        sessionData["images_360"] = images_360
        with open(os.path.join(inputDir,sessionFile), 'w') as outfile:  
            json.dump(sessionData, outfile)


root = tk.Tk()
root.withdraw()
dir2Scan = filedialog.askdirectory(initialdir = os.path.dirname(os.path.realpath(__file__)))
scanFolder(dir2Scan)

