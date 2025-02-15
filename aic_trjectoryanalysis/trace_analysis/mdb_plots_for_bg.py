'''
[DONE]
this program writes all [ID, camera, [x], [y]] from gt.txt files for visualization
#? we don't need to seperate train folder & validation folder since we can pick what to use in our simulation 
#! if you have time, change this to reading from gt db instead of reading the files :S
'''
import os, sys, time
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
from pymongo import MongoClient

#* connect to mongodb
client = MongoClient('localhost', 27017)
db = client['aic_mtmc']
mdb = db['draw_traces']

allfiles=[]

def get_camid_section(filename):
    camid, section = None, None
    items = filename.split('/')
    for item in items:
        if item.startswith("c0"):
            camid = item
        if item.startswith("S"):
            section = item
    return camid, section

#* iterate through folder to find all gt.txt files.
for (path, dir, files) in os.walk ("/home/spencer1/samplevideo/AIC20_track3_MTMC/"):
    for filename in files:
        ext = os.path.splitext(filename)[-1]
        if ext == ".txt" and "gt" in os.path.splitext(filename)[0]:
            #print("%s/%s" % (path, filename))
            allfiles.append(path+"/"+filename)
count=0
for file in tqdm(allfiles):
    xplots = []
    yplots = []
    #print(count)
    if os.stat(file).st_size != 0:
        df = pd.read_csv(file, header=None, delimiter=',')
        items = defaultdict(lambda: defaultdict(list))
        camid, section = get_camid_section(file)
        for index, row in df.iterrows(): #[frame, ID, left, top, width, height, 1, -1, -1, -1]
            #* however many ids there are.            
            centx = row[2] + (row[4] / 2)
            centy = row[3] + (row[5] / 2)

            items[row[1]]["x"].append(centx) #id, x: list, y: list
            items[row[1]]["y"].append(centy)
            #print(row[1])

            
        #print(items[row[1]]["x"], items[row[1]]["y"])   
        #print(len(items))
        for i in (items):
            #print(i)
            inputrow = {"uid": str(i), "section": str(section), "camid": str(camid), "x": items[i]["x"], "y": items[i]["y"]}
            print(inputrow)
            mdb.insert_one(inputrow)
            count+=1

