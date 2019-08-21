# -*- coding: utf-8 -*-
import socket
import time
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    data='A'*1024
    print len(data)
    sock.sendto(data, ('149.129.81.250', 9090))
    #sock.sendto(data, ('149.129.90.120', 9090))
    #sock.sendto(data, ('127.0.0.1', 9090))
    time.sleep(0.01)
    print "send msg"
 
    
