import argparse
import sys
import numpy as np

import string
import random
import cv2
import math
import glob
import time
import json

def main():
    json_data=open("QRCodeLocations.json").read()
    data = json.loads(json_data)
    for x in data:
        img = cv2.imread(x['image_path'])
        cv2.rectangle(img,(x['rects'][0]['x1'],x['rects'][0]['y1']),(x['rects'][0]['x2'],x['rects'][0]['y2']),(0,255,0),2)
        cv2.imshow('image',img)
        key = cv2.waitKey(0)
        if key == 27:
            break
        else:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
