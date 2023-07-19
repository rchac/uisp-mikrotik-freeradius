import csv
import os
import requests
from subprocess import call
from datetime import datetime, date
from routeros_api2 import Api
import subprocess
import ipaddress
import json
from ipaddress import IPv4Address, IPv4Network
from configFile import baseURL, xAuthToken, validNetworks, notAllowed, edgeRouterIP, edgeRouterUser, edgeRouterPassword

def isIPv4valid(ipv4):
	isValid = False
	
	if IPv4Address(ipv4) not in notAllowed:
		for network in validNetworks:
			if IPv4Address(ipv4) in network:
				isValid = True
	
	return isValid
	
def updateRadius():
	print("Initiating updateRadius at " + datetime.now().strftime("%d/%m/%Y"))	
	url = baseURL + "sites?type=client&ucrm=true&ucrmDetails=true"
	headers = {'accept':'application/json', 'x-auth-token': xAuthToken}
	r = requests.get(url, headers=headers)
	jsonData = r.json()
	listOfSuspendedClients = []
	listOfNonSuspendedMACs = []
	whiteListedMACs = []
	whiteListedIPs = []

	url = baseURL + "devices?type=airCube&role=ap"
	headers = {'accept':'application/json', 'x-auth-token': xAuthToken}
	r5 = requests.get(url, headers=headers)
	allAirCubes = r5.json()

	url = baseURL + "devices?type=blackBox"
	headers = {'accept':'application/json', 'x-auth-token': xAuthToken}
	r4 = requests.get(url, headers=headers)
	allBlackBoxes = r4.json()

	for site in jsonData:
		isSuspended = site['identification']['suspended']
		foundCPEforClient = False
		siteID = site['identification']['id']
		
		#Get AirCubes
		for aircube in allAirCubes:
			if aircube['identification']['site']['id'] == siteID:
				name = aircube['identification']['name']
				mac = aircube['identification']['mac']
				ipv4 = aircube['ipAddress']
				if '/' in ipv4:
					ipv4 = ipv4.split('/')[0]
				if isIPv4valid(ipv4):
					if (name != None) and (mac != None):
						if isSuspended:
							listOfSuspendedClients.append((name,mac,ipv4))
						else:
							listOfNonSuspendedMACs.append((name,mac))
							whiteListedMACs.append(mac)
							whiteListedIPs.append(ipv4)
						foundCPEforClient = True
		
		#Get BlackBox Devices
		for blackbox in allBlackBoxes:
			if blackbox['identification']['site']['id'] == siteID:
				hostnameUpper = blackbox['identification']['hostname'].upper()
				if ('CPE-' in hostnameUpper) or ('MIKROTIK-' in hostnameUpper) or ('AIRCUBE-' in hostnameUpper):
					name = blackbox['identification']['hostname']
					mac = blackbox['identification']['mac']
					ipv4 = blackbox['ipAddress']
					if '/' in ipv4:
						ipv4 = ipv4.split('/')[0]
					if isIPv4valid(ipv4):
						if (name != None) and (mac != None):
							if isSuspended:
								listOfSuspendedClients.append((name,mac,ipv4))
							else:
								whiteListedIPs.append(ipv4)
								if mac != "":
									listOfNonSuspendedMACs.append((name,mac))
									whiteListedMACs.append(mac)
								
							foundCPEforClient = True
		
		if not foundCPEforClient:
			print("Failed to find associated CPE for " + site['identification']['name'])
	
	#with open('users.input.txt', 'r') as f:
	#	for line in f:oldUsersFile = f.readlines()
	my_file = open("users.input.txt", "r")
	oldUsersFile = my_file.read()
	my_file.close()
	
	with open('/etc/freeradius/3.0/users', 'w') as the_file:
		for device in listOfNonSuspendedMACs:
			#print(device)
			hostname, mac = device
			mac = mac.upper().replace('-',':')
			mac = mac.upper().replace(':','')
			lineToWrite = mac + ' Auth-Type := Accept'
			the_file.write(lineToWrite + '\n')
		for line in oldUsersFile:
			the_file.write(line)
			#the_file.write('\n')
			
	with open('/etc/freeradius/3.0/authorized_macs', 'w') as the_file:
		for device in listOfNonSuspendedMACs:
			#print(device)
			hostname, mac = device
			mac = mac.upper().replace('-',':')
			mac = mac.upper().replace(':','')
			the_file.write(mac + '\n')
			the_file.write('        Reply-Message = "Device with MAC Address %{Calling-Station-Id} authorized for network access"' + '\n')
			the_file.write('\n')
	
	
	#Reload freeradius, to ensure IPv6 works (users file is only used on restart of freeradius)
	print(subprocess.Popen('sudo systemctl restart freeradius.service', shell=True, stdout=subprocess.PIPE).stdout.read())
	
	#Revise suspended
	revisedSuspended = []
	for client in listOfSuspendedClients:
		name,mac,ipv4 = client
		if mac not in whiteListedMACs:
			if ipv4 not in whiteListedIPs:
				revisedSuspended.append(client)
		else:
			print("Error")
	
	#Get IPs only
	ipv4AddressesToSuspend = []
	ipv6AddressesToSuspend = []
	ipv4ToIPv6 = {}
	f = open('ipv4ToIPv6.json')
	ipv4ToIPv6 = json.load(f)
	
	for client in revisedSuspended:
		name,mac,ipv4 = client
		if ipv4 in ipv4ToIPv6:
			ipv6 = ipv4ToIPv6[ipv4]
			if ipv6 not in ipv6AddressesToSuspend:
				ipv6AddressesToSuspend.append(ipv6)
				#print(ipv6)
			else:
				print('Problem detected. Duplicate IPv6 on suspension list.')
		ipv4AddressesToSuspend.append(ipv4)
	
	#Print suspended
	print("The following clients will be suspended")
	for client in revisedSuspended:
		name,mac,ipv4 = client
		print("Name: " + name + " MAC: " + mac + " IP: " + ipv4)
	
	try:
		#Log into mikrotik and suspend IPv4s
		router = Api(edgeRouterIP, user=edgeRouterUser, password=edgeRouterPassword, port=8729, verbose=False, use_ssl=True)
		r = router.talk('/ip/firewall/address-list/print where list=uisp_suspended')

		ipv4ExistingFirewallListIDs = {}
		ipv4ExistingFirewallListIPs = []
		for element in r:
			idNum = element['.id']
			listID = element['list']
			address = element['address']
			if listID == "uisp_suspended":
				#print("ID: " + idNum + " List: " + listID + " IP: " + address)
				ipv4ExistingFirewallListIPs.append(address)
				ipv4ExistingFirewallListIDs[address] = idNum

		#Delete superflouous IPs
		for ip in ipv4ExistingFirewallListIPs:
			if ip not in ipv4AddressesToSuspend:
				#Delete IP
				message = '/ip/firewall/address-list/remove\n=numbers=' + ipv4ExistingFirewallListIDs[ip]
				print("Deleting IP: " + ip)
				r = router.talk(message)

		for ip in ipv4AddressesToSuspend:
			if ip not in ipv4ExistingFirewallListIPs:
				#Delete IP
				message = '/ip/firewall/address-list/add\n=address=' + ip + '\n=list=uisp_suspended'
				print("Adding IP: " + ip)
				r = router.talk(message)
		
		r = router.talk('/ipv6/firewall/address-list/print where list=uisp_suspended')

		ipv6ExistingFirewallListIDs = {}
		ipv6ExistingFirewallListIPs = []
		for element in r:
			idNum = element['.id']
			listID = element['list']
			address = element['address']
			if listID == "uisp_suspended":
				#print("ID: " + idNum + " List: " + listID + " IP: " + address)
				ipv6ExistingFirewallListIPs.append(address)
				ipv6ExistingFirewallListIDs[address] = idNum

		#Delete superflouous IPs
		for ip in ipv6ExistingFirewallListIPs:
			if ip not in ipv6AddressesToSuspend:
				#Delete IP
				message = '/ipv6/firewall/address-list/remove\n=numbers=' + ipv6ExistingFirewallListIDs[ip]
				print("Deleting IP: " + ip)
				r = router.talk(message)

		for ip in ipv6AddressesToSuspend:
			if ip not in ipv6ExistingFirewallListIPs:
				#Delete IP
				message = '/ipv6/firewall/address-list/add\n=address=' + ip + '\n=list=uisp_suspended'
				print("Adding IP: " + ip)
				r = router.talk(message)

	except:
		print("Failed to update MikroTik Edge")
	print("Completed updateRadius at " + datetime.now().strftime("%d/%m/%Y"))
if __name__ == '__main__':
	updateRadius()
