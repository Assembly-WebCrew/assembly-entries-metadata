import os.path
import urllib2

def argparseTypeUrlOpenable(value):
    filePath = value
    if os.path.exists(filePath):
        filePath = "file://%s" % filePath

    return urllib2.urlopen(filePath)
