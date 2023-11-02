# UISP MikroTik & FreeRadius Integration Script

This script allows Internet Service Providers which use UISP to suspend client traffic transiting their MikroTik routers.
It also allows for restricting DHCP leases to only the equipment IPs of known customers.

## Purpose
This is primarily meant to be a starting point for your own integration. It assumes certain things like that you have a dual stack IPv4/IPv6 network.
You can modify the code to suit your needs.

## Requirements
- A self-hosted UISP instance (not hosted by Ubiquiti)
- A VM to run this on, running Ubuntu Server 22.04 or more recent. 
- FreeRadius installed on the same VM
- A MikroTik Edge Router (to block suspended IPs, do NAT)
- 1 or more MikroTik routers acting as your DHCP server
- MikroTik ROS on these routers can be v6 or v7

## Overview

## How it works

This script pulls customer IP addresses from UISP.
Customer equipment MAC addresses are added to FreeRadius' allowed MAC addresses.
This allows you to do basic DHCP auth to prevent unauthorized DHCP leases.
You would toggle the radius option for your DHCP server and enable radius for the mikrotiks that hand out your DHCP leases.
Define your DHCP server mikrotiks in ```mikrotikDHCPRouterList.csv```
For suspended customers, their corresponding IP addresses are added to a MikroTik firewall list "uisp_suspended".

Suspended clients will have traffic redirected to your UISP instance IP address via this NAT rule.

```
add action=dst-nat chain=dstnat comment="UISP Suspension" dst-port=80 \
    protocol=tcp src-address-list=uisp_suspended to-addresses=1.2.3.4 \
    to-ports=81
add action=dst-nat chain=dstnat dst-port=443 protocol=tcp src-address-list=\
    uisp_suspended to-addresses=1.2.3.4 to-ports=81
```
Add this to the top of your firewall NAT entries, replacing 1.2.3.4 with your local UISP server IP address.

Suspended clients will have any non-UISP traffic blocked by these rules (add them to the top of your firewall filter list):
```
/ip firewall filter
add action=drop chain=forward comment=\
    "UISP Auto Suspension via RADIUS server script" dst-address-list=\
    uisp_suspended in-interface-list=WAN
add action=drop chain=forward out-interface-list=WAN src-address-list=\
    uisp_suspended
```
Make sure WAN corresponds to an appropriate WAN interface list on your MikroTik Edge

## Settings
Modify configFile.py to match your network and UISP settings.

## Test functionality

Test functionality first using ```sudo python3 scheduled.py```

Once you have it able to run successfully, proceed to create a systemd service.

## Running as a service

Create a systemd file ```/etc/systemd/system/uispRadius.service``` by modifying the file uispRadius.service included in this project.
Replace YOUR_USER with your user.

Then run
```sudo systemctl daemon-reload```
And
```sudo systemctl enable uispRadius```
```sudo systemctl start uispRadius```
