import time
import schedule
from datetime import datetime, date
from uispRadius import updateRadius
from getIPv6 import pullMikrotikIPv6
import warnings
import signal
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

def handler(signum, frame):
	#print("Function took over 20 seconds to complete.")
	raise Exception("Function took over 660 seconds to complete.")

def updateRadiusHandler():
	#signal.signal(signal.SIGALRM, handler)
	#secondThreshold = (60*10) + 60
	#signal.alarm(secondThreshold)
	try:
		updateRadius()
		print("Successfully ran updateRadius at " + datetime.now().strftime("%d/%m/%Y"))
	except:
		print("Failed to run updateRadius at " + datetime.now().strftime("%d/%m/%Y"))

def getIPv6FromMACHandler():
	#signal.signal(signal.SIGALRM, handler)
	#secondThreshold = (60*10) + 60
	#signal.alarm(secondThreshold)
	try:
		pullMikrotikIPv6()
		print("Successfully ran pullMikrotikIPv6 at " + datetime.now().strftime("%d/%m/%Y"))
	except:
		print("Failed to run pullMikrotikIPv6 at " + datetime.now().strftime("%d/%m/%Y"))

if __name__ == '__main__':
	ads = BlockingScheduler(executors={'default': ThreadPoolExecutor(1)})
	
	updateRadiusHandler()
	#getIPv6FromMACHandler()
	
	ads.add_job(updateRadiusHandler, 'interval', minutes=30, max_instances=1)
	#ads.add_job(getIPv6FromMACHandler, 'interval', minutes=5)

	ads.start()
