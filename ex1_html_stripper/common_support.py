import time
startTime = 0
def startTimer():
	global startTime
	startTime = time.time()
def stopTimer():
	stopTime = time.time()
	return stopTime-startTime
def getTimer():
	currentTime = time.time()
	elaTime = currentTime - startTime
	string = "%.2f" % elaTime()
	return string
def printTimer():
	string = "%.2f" % stopTimer()
	return string