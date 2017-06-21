#!/usr/bin/env python
import sys
import time
import dpkt
import struct
import binascii
from socket import *

f = open(sys.argv[1])
pcap = dpkt.pcap.Reader(f)

skipcnt = 0
firstkeyframe = 0
rtpseq = -1
client = socket(AF_INET, SOCK_DGRAM)
ADDR = ("192.168.127.87", 19000) 
doInterval = 0
prevTS = -1
PACKET_SEND_WAIT = 1

for ts, buf in pcap:
    if pcap.dloff == 14:
        eth = dpkt.ethernet.Ethernet(buf)
    elif pcap.dloff == 16:
        eth = dpkt.sll.SLL(buf)
    else:
        print pcap.dloff,'is unknown'
    if eth.data.__class__.__name__ =='IP':
        ip = eth.data
        if ip.data.__class__.__name__=='UDP':
            udp = ip.data

            try:
                rtp = dpkt.rtp.RTP(udp.data)
                client.sendto(udp.data,ADDR)  
                if prevTS != -1:                    
                    time.sleep(float(ts - prevTS))
                prevTS = ts
            except dpkt.dpkt.NeedData:
                continue
            except dpkt.dpkt.UnpackError:
                continue
f.close()

