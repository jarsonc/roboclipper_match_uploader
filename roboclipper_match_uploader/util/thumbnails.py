from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

def generateThumbnail(eventName, eventType):
    fin = open("../thumbnailAssets/default_template.svg", "rt")
    data = fin.read()
    data = data.replace('Line1', eventName)
    data = data.replace('Line2', eventType)
    fin.close()

    fileName = eventName.replace(" ", "").lower() + "_" + eventType.replace(" ", "").lower()
    fin = open(fileName + ".svg", "wt")
    fin.write(data)
    fin.close()

    renderPM.drawToFile(svg2rlg(fileName+".svg"), fileName+".png", fmt="PNG")

