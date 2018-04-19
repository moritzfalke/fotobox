import json
import datetime
from os import path

pictureCount = 0
data = {}


def createFile():
    if not(path.isfile("data.json")):
        global data
        f = open("data.json", "w")
        data = {}
        json.dump(data, f, indent=5)
        f.close()


def readData():
    global data
    global pictureCount
    with open('data.json') as json_file:
        data = json.load(json_file)
        if(str(datetime.date.today()) in data):
            pictureCount = data[str(datetime.date.today())]


def writeData():
    global data
    data = {}
    data[str(datetime.date.today())] = pictureCount

    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, indent=5)


def increasePictureCounter():
    global pictureCount
    pictureCount += 1
    writeData()


def getPictureCounter():
    global pictureCount
    return pictureCount


createFile()
readData()
increasePictureCounter()
increasePictureCounter()
print(datetime.date.today())
print(getPictureCounter())
