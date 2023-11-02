import time
import schedule
from datetime import datetime, date
from uispRadius import updateRadius
from getIPv6 import pullMikrotikIPv6
import warnings
import signal

def handler(signum, frame):
	#print("Function took over 20 seconds to complete.")
	raise Exception("Function took over 660 seconds to complete.")

def updateRadiusHandler():
	signal.signal(signal.SIGALRM, handler)
	secondThreshold = (60*2)
	signal.alarm(secondThreshold)
	try:
		updateRadius()
		print("Successfully ran updateRadius at " + datetime.now().strftime("%d/%m/%Y"))
	except:
		print("Failed to run updateRadius at " + datetime.now().strftime("%d/%m/%Y"))

def getIPv6FromMACHandler():
	signal.signal(signal.SIGALRM, handler)
	secondThreshold = (60*2)
	signal.alarm(secondThreshold)
	try:
		pullMikrotikIPv6()
		print("Successfully ran pullMikrotikIPv6 at " + datetime.now().strftime("%d/%m/%Y"))
	except:
		print("Failed to run pullMikrotikIPv6 at " + datetime.now().strftime("%d/%m/%Y"))

if __name__ == '__main__':

	while(True):
		getIPv6FromMACHandler()
		updateRadiusHandler()
		time.sleep(60*10)
