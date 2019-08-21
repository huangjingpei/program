#!/usr/bin/python 
#encoding=utf-8
import select
import socket
import Queue
import time
 
#create a socket
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setblocking(False)
#set option reused
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR  , 1)
 
server_address= ('0.0.0.0',10001)
server.bind(server_address)
 
server.listen(10)
 
#sockets from which we except to read
inputs = [server]
 
#sockets from which we expect to write
outputs = []
 
#Outgoing message queues (socket:Queue)
message_queues = {}
 
#A optional parameter for select is TIMEOUT
timeout = 20

while inputs:
	print "waiting for next event"
	readable , writable , exceptional = select.select(inputs, outputs, inputs, timeout)
 
	# When timeout reached , select return three empty lists
	if not (readable or writable or exceptional) :
	    continue;    
	for s in readable :
	    if s is server:
	        # A "readable" socket is ready to accept a connection
	        connection, client_address = s.accept()
	        print "    connection from ", client_address
	        connection.setblocking(0)
	        inputs.append(connection)
	        message_queues[connection] = Queue.Queue()
	    else:
	        data = s.recv(1024)
	        if data :
	            print "time ", time.asctime(time.localtime(time.time())), "from ",s.getpeername()
	            message_queues[s].put(data)
	            # Add output channel for response    
	            if s not in outputs:
	                outputs.append(s)
	        else:
	            #Interpret empty result as closed connection
	            print "  closing", client_address
	            if s in outputs :
	                outputs.remove(s)
	            inputs.remove(s)
	            s.close()
	            #remove message queue 
	            del message_queues[s]
	for s in writable:
		try:
			next_msg = message_queues[s].get_nowait()
		except Queue.Empty:
			#print " " , s.getpeername() , 'queue empty'
			outputs.remove(s)
		else:
			#print " sending " , next_msg , " to ", s.getpeername()
			#s.send(next_msg)
			pass
			
	 
	for s in exceptional:
	    print " exception condition on ", s.getpeername()
	    #stop listening for input on the connection
	    inputs.remove(s)
	    if s in outputs:
	        outputs.remove(s)
	    s.close()
	    #Remove message queue
	    del message_queues[s]
