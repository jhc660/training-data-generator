import argparse
import sys
import numpy as np

import string
import random
import cv2
import pyqrcode
import math
import glob
import time
import json

#Tweakable Variables
log_type = "JSON"
size = 100
fuzz_ratio = 7
random_displacement_ratio = 2
final_size = (640,480)

def main():
    global log_type

    #All JPGs in directory and subdirectories will be modified
    files = glob.glob('**/*.jpg', recursive=True)
    number = len(files)
    cur = 0
    start = time.clock()
    
   
    #Write Header for the document if JSON
    if log_type == "JSON":
        document = open("QRCodeLocations.json", "w")
        document.write('[\n')
    else:
        document = open("QRCodeLocations.txt", "w")

    #Iterate through all files.
    for x in files:
        cur+=1
        print("completed "+str(cur)+" out of "+str(number))
        average_time = (time.clock()-start)/cur
        remaining_count = number-cur
        print("estimated time: " + str(average_time*remaining_count/60) + " minutes")
        generate_image(x, document) 

        #Seperate json values by comma
        if (log_type == "JSON") and (cur<number):
            document.write(',\n')
    
    print("total time taken: " + str((time.clock()-start)/60) + " minutes")

    #Write Endnote for the document if JSON
    if log_type == "JSON":
        document.write(']')
    
    document.close()
 
def generate_image(name, log):
    global log_type
    global size
    global final_size
    global fuzz_ratio
    global random_displacement_ratio

    #Generate random QR
    text = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    qr = pyqrcode.create(text)
    qr.png("qr.png", scale=6)

    #Load generated QR (There might be a way to load QR without having to save it to disk first)
    image = cv2.imread("qr.png", 0)
    rows,cols = image.shape
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)

    #Define two sets of point for transformation
    fuzz = int(size/fuzz_ratio)
    pts1 = np.float32([[0,0],[cols,0],[0,rows],[cols,rows]])
    pts2 = np.float32([[0+random.randint(0,fuzz),0+random.randint(0,fuzz)],[size-random.randint(0,fuzz),0+random.randint(0,fuzz)],[0+random.randint(0,fuzz),size-random.randint(0,fuzz)],[size-random.randint(0,fuzz),size-random.randint(0,fuzz)]]) 
  
    #Obtain Perspective Transform
    M = cv2.getPerspectiveTransform(pts1,pts2)
    transform = cv2.warpPerspective(image,M,(size,size), borderValue = 0)
    
    #Blur QR Code Image
    dst = cv2.GaussianBlur(transform,(5,5),0)

    #Read destination image
    testIm = cv2.imread(name,1)
    testIm = cv2.resize(testIm, dsize = final_size)
    rows, cols, ch = testIm.shape
    testIm = cv2.cvtColor(testIm, cv2.COLOR_RGB2RGBA)

    disp_fuzz_x = int(cols/random_displacement_ratio)
    disp_fuzz_y = int(rows/random_displacement_ratio)
    qr_origin = ((cols/2+random.randint(-disp_fuzz_x,disp_fuzz_x)), (rows/2+random.randint(-disp_fuzz_y,disp_fuzz_y)))
    pts2+=qr_origin
    blendedImage = blend_image(testIm, dst, qr_origin)
    cv2.imwrite(name+".png", blendedImage)

    #Log the location of the QR code for each image.
    if log_type == "CSV":
        write_CSV(log, name, pts2[0], pts2[1], pts2[2], pts2[3])
    elif log_type == "JSON":
        write_JSON_TensorBox(log, name, pts2[0], pts2[1], pts2[2], pts2[3], cols, rows)

#Combine two images. Note: This is a simplified algorithm that assumes the baseImage is fully opaque and the addImage has binary alphas.
def blend_image(baseImage, addImage, location):
    returnImage = baseImage.copy()
    for x in range(addImage.shape[0]):
        for y in range(addImage.shape[1]):
            r_x = int(location[1]+x)
            r_y = int(location[0]+y)
            if (0<=r_x<baseImage.shape[0]) and (0<=r_y<baseImage.shape[1]) > 0:
                a_add = addImage[x][y][3]/255
                returnImage[r_x][r_y][0] = (addImage[x][y][0]*a_add) + baseImage[r_x][r_y][0]*(1-a_add)
                returnImage[r_x][r_y][1] = (addImage[x][y][1]*a_add) + baseImage[r_x][r_y][1]*(1-a_add)
                returnImage[r_x][r_y][2] = (addImage[x][y][2]*a_add) + baseImage[r_x][r_y][2]*(1-a_add)
    return returnImage

def write_CSV(log_name, file_name, point1, point2, point3, point4):
    log_name.write(file_name+", "+str(point1[0])+", "+str(point1[1])+", "+str(point2[0])+", "+str(point2[1])+", "+str(point3[0])+", "+str(point3[1])+", "+str(point4[0])+", "+str(point4[1])+'\n')

def write_JSON_TensorBox(log_name, file_name, point1, point2, point3, point4, max_x, max_y):
    x1 = min(point1[0],point2[0],point3[0],point4[0])
    x2 = max(point1[0],point2[0],point3[0],point4[0])
    y1 = min(point1[1],point2[1],point3[1],point4[1])
    y2 = max(point1[1],point2[1],point3[1],point4[1])
    enforce boundary values
    if x1<0:
        x1 = 0
    if x1>(max_x-1):
        x1 = (max_x-1)

    if y1<0:
        y1 = 0
    if y1>(max_y-1):
        y1 = (max_y-1)

    if x2<0:
        x2 = 0
    if x2>(max_x-1):
        x2 = (max_x-1)

    if y2<0:
        y2 = 0
    if y2>(max_y-1):
        y2 = (max_y-1)
    
    if (x1!=x2) and (y1!=y2):
        log_name.write(json.dumps({"image_path":file_name+".png", "rects":({"x1":int(x1), "x2":int(x2), "y1":int(y1), "y2":int(y2)},)}, indent = 2))

if __name__ == "__main__":
    main()
