#!/usr/bin/python
#encoding=utf-8
 
import socket
import time 
messages = ["This is the message" ,
            "It will be sent" ,
            "in parts "]
 
print "Connect to the server"
#server_address = ("149.129.81.250",9090)
server_address = ("122.112.196.151",9090)
#server_address = ("0.0.0.0",10001)
#Create a TCP/IP sock
socks = []
#for i in range(10):
#    socks.append(socket.socket(socket.AF_INET,socket.SOCK_STREAM))
#for s in socks:
#    s.connect(server_address)
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
s.connect(server_address)
print "CONNECT"
counter = 0
#for message in messages :
    #Sending message from different sockets
#    for s in socks:
#        counter+=1
#        print "  %s sending %s" % (s.getpeername(),message+" version "+str(counter))
#        s.send(message+" version "+str(counter))
#    #Read responses on both sockets
#    for s in socks:
#        data = s.recv(1024)
#        print " %s received %s" % (s.getpeername(),data)
#        if not data:
#            print "closing socket ",s.getpeername()
#
#            s.close()


while True :
    data = 'A'*1024
    s.send(data)
    print "SEND"
    time.sleep(0.1)
    #data = s.recv(1024) 
s.close()
