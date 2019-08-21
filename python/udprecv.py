# -*- coding: utf-8 -*-
import socket 
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)  
sock.settimeout(2.0)
sock.bind(('0.0.0.0', 9090))
last = time.time()
now = last
while True:
    try:
        data, addr = sock.recvfrom(1024)
        now = time.time();
        print "recv data:", data
        #if (now - last > 2.0) :
            #print "no data to receive"
    except socket.timeout:
        print "no data to receive"
        
    #print "now:", now
    last = now

sock.close()
