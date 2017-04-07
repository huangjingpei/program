#!/usr/bin/env python
import httplib
import json
import socket
import sys


class Channel:
	connection_type = 'keep-alive'
	def __init__(self,_channel_number,media_port,buffer,dstaddr,s,_conn):
		self._channel_number = _channel_number
		self.media_port = media_port
		self.buffer = buffer
		self.dstaddr = dstaddr
		self.s = s
		self._conn = _conn
		
	def get_head_lines(self, name):
		lines = self.buffer.split('\r\n')
		lines_lens = len(lines) - 1
		for i in range(0,lines_lens):
			if lines[i].find(name) == 0:
				return lines[i]

	def get_gvc_media_address_line(self):
		lines = self.buffer.split('\r\n')
		lines_lens = len(lines) - 1
		for i in range(0,lines_lens):
			if lines[i].find("c=IN") == 0:
				return lines[i]

	def get_gvc_audio_port_line(self):
		lines = self.buffer.split('\r\n')
		lines_lens = len(lines) - 1
		for i in range(0,lines_lens):
			if lines[i].find("m=audio") == 0:
				return lines[i]

	def get_gvc_video_port_line(self):
			lines = self.buffer.split('\r\n')
			lines_lens = len(lines) - 1
			for i in range(0,lines_lens):
					if lines[i].find("m=video") == 0:
							return lines[i]

	def get_mcu_audio_port(self):
		mcu_audio_port = self.media_port[0]
		self.media_port.pop(0)
		print "MCU Audio Port: ",mcu_audio_port
		return mcu_audio_port
		
	def get_mcu_video_port(self):
		mcu_video_port = self.media_port[0]
		self.media_port.pop(0)
		print "MCU Video Port: ",mcu_video_port
		return mcu_video_port
	
	def get_gvc_media_address(self):
		gvc_media_ipaddress = self.get_gvc_media_address_line()[9:24]
		print "Remote GVC's Media Information:"
		print "GVC IP Address: ",gvc_media_ipaddress
		return gvc_media_ipaddress
	
	def get_gvc_audio_port(self):
		gvc_audio_port = self.get_gvc_audio_port_line()[8:12]
		print "GVC Audio Port: ",gvc_audio_port
		return gvc_audio_port
	
	def get_gvc_video_port(self):
		gvc_video_port = self.get_gvc_video_port_line()[8:12]
		print "GVC Video Port: ",gvc_video_port
		return gvc_video_port
	
	def response_100(self):
		recv_via = self.get_head_lines("Via")
		recv_from = self.get_head_lines("From")
		recv_to = self.get_head_lines("To")
		recv_call_id = self.get_head_lines("Call-ID")
		recv_cseq = self.get_head_lines("CSeq")
		header_data = "SIP/2.0 100 Trying\r\n"
		header_data += recv_via + "=5060\r\n"
		header_data += recv_from + "\r\n"
		header_data += recv_to + "\r\n"
		header_data += recv_call_id + "\r\n"
		header_data += recv_cseq + "\r\n"
		header_data += "User-Agent: Python Server\r\n"
		header_data += "Allow: INVITE, ACK, OPTIONS, CANCEL, BYE, SUBSCRIBE, NOTIFY, INFO, REFER, UPDATE, MESSAGE\r\n"
		header_data += "Content-Length:0\r\n\r\n"
		self.s.sendto(header_data,self.dstaddr)

	def response_180(self):
		recv_via = self.get_head_lines("Via")
		recv_from = self.get_head_lines("From")
		recv_to = self.get_head_lines("To")
		recv_call_id = self.get_head_lines("Call-ID")
		recv_cseq = self.get_head_lines("CSeq")
		header_data = "SIP/2.0 180 Ringing\r\n"
		header_data += recv_via + "\r\n"
		header_data += recv_from + "\r\n"
		header_data += recv_to + ";tag=20151219\r\n" 
		header_data += recv_call_id + "\r\n"
		header_data += recv_cseq + "\r\n"
		header_data += "Contact: <sip:4000@" + local_sip_address + ":" + str(local_sip_port) + ">\r\n"
		header_data += "User-Agent: Python Server\r\n"
		header_data += "Allow: INVITE, ACK, OPTIONS, CANCEL, BYE, SUBSCRIBE, NOTIFY, INFO, REFER, UPDATE, MESSAGE\r\n"
		header_data += "Content-Length:0\r\n\r\n"
		self.s.sendto(header_data,self.dstaddr)

	def response_200(self):
		recv_via = self.get_head_lines("Via")
		recv_from = self.get_head_lines("From")
		recv_to = self.get_head_lines("To") 
		recv_call_id = self.get_head_lines("Call-ID")
		recv_cseq = self.get_head_lines("CSeq")
		sdp_data = "v=0\r\n"
		sdp_data += "o=4000 8000 8000 IN IP4 " + src_media_address + "\r\n"
		sdp_data += "s=SIP Call\r\n"
		sdp_data += "c=IN IP4 " + src_media_address +"\r\n"
		sdp_data += "t=0 0\r\n"
		sdp_data += "m=audio " + str(self._bind_audio_port) + " RTP/AVP 0 101\r\n"
		sdp_data += "a=sendrecv\r\n"
		sdp_data += "a=rtpmap:0 PCMU/8000\r\n"
		sdp_data += "a=ptime:20\r\n"
		sdp_data += "a=101 telephone-event/8000\r\n"
		sdp_data += "a=fmtp:101 0-15\r\n"
		sdp_data += "m=video " + str(self._bind_video_port) + " RTP/AVP 99 120\r\n"
		sdp_data += "b=AS:2240\r\n"
		sdp_data += "a=sendrecv\r\n"
		sdp_data += "a=rtpmap:99 H264/90000\r\n"
		sdp_data += "a=fmtp:99 profile-level-id=428028; packetization-mode=1\r\n"
		sdp_data += "a=rtpmap:120 GS-FEC/90000\r\n"
		sdp_data += "a=gs-fec-version:1\r\n"
		sdp_data += "a=framerate:30\r\n"
		sdp_data += "a=content:main\r\n"
		sdp_data += "a=label:11\r\n"
		header_data = "SIP/2.0 200 OK\r\n"
		header_data += recv_via + "=5060\r\n"
		header_data += recv_from + "\r\n"
		header_data += recv_to + ";tag=20151219\r\n"
		header_data += recv_call_id + "\r\n"
		header_data += recv_cseq + "\r\n"
		header_data += "Contact: <sip:4000@" + local_sip_address + ":" + str(local_sip_port) + ">\r\n"
		header_data += "User-Agent: Python Server\r\n"
		header_data += "Allow: INVITE, ACK, OPTIONS, CANCEL, BYE, SUBSCRIBE, NOTIFY, INFO, REFER, UPDATE, MESSAGE\r\n"
		header_data += "Content-Type: application/sdp\r\n"
		header_data += "Content-Length: " + str(len(sdp_data)) + "\r\n\r\n"
	#	header_data += "m=application 0 UDP/BFCP *\r\n"
	#	header_data += "m=video 0 RTP/AVP 99\r\n"
	#	header_data += "m=application 0 RTP/AVP 125\r\n"
		self.s.sendto(header_data+sdp_data,self.dstaddr)
		
	def response_200_to_BYE(self):
		recv_via = self.get_head_lines("Via")
		recv_from = self.get_head_lines("From")
		recv_to = self.get_head_lines("To") 
		recv_call_id = self.get_head_lines("Call-ID")
		recv_cseq = self.get_head_lines("CSeq")
		header_data = "SIP/2.0 200 OK\r\n"
		header_data += recv_via + "=5060\r\n"
		header_data += recv_from + "\r\n"
		header_data += recv_to + ";tag=20151219\r\n"
		header_data += recv_call_id + "\r\n"
		header_data += recv_cseq + "\r\n"
		header_data += "Contact: <sip:4000@" + local_sip_address + ":" + str(local_sip_port) + ">\r\n"
		header_data += "User-Agent: Python Server\r\n"
		header_data += "Allow: INVITE, ACK, OPTIONS, CANCEL, BYE, SUBSCRIBE, NOTIFY, INFO, REFER, UPDATE, MESSAGE\r\n"
		header_data += "Content-Type: application/sdp\r\n"
		header_data += "Content-Length: 0\r\n\r\n"
		self.s.sendto(header_data,self.dstaddr)
	
	def channelStart(self):
		_gvc_media_ipaddress = self.get_gvc_media_address()
		self._bind_audio_port = self.get_mcu_audio_port()
		self._bind_video_port = self.get_mcu_video_port()
		_remote_audio_port = self.get_gvc_audio_port()
		_remote_video_port = self.get_gvc_video_port()
		headers ={
			"Content-Type":"application/json",
			"Connection":self.connection_type
			}

		msg=[{

			"avs_setparam":{
			"conf_id":"0_M",
			"chan_id":"0",
			#"audio_enc_param":{
			#	"MainCoder":"audio/pcmu",
			#	"CN":"0",
			#	"PayloadType":"0",
			#	"Ptime":"10"
			#	},
			#"audio_dec_param":{
			#	"Codecs":"audio/pcmu",
			#	"PayloadType":"0",
			#	},
			#"audio_transport":{
			#	"BindPort":"5004",
			#	"TargetAddr":"192.168.127.33:5004",
			#	"SymRTP":"0",
			#	"rtcp-mux":"0"
			#	},
			"video_enc_param":{
				"MainCoder":"video/avc",
				"ImageSize":"704x576",
				"FrameRate":"15",
				"Profile":"HP",
				"BitRate":"1024000",
				"PayloadType":"99"#,
                #"FecPT":"126",
                #"RedPT":"127",
                #"FecType":"1"
				},
			"video_dec_param":{
				"Codecs":"video/avc",
				"ImageSize":"1280x720",
				"FrameRate":"15",
				"PayloadType":"99",
                "FecPT":"126",
                "RedPT":"127",
                "FecType":"1"
				},
			"video_transport":{
				"BindPort":"5006",
				"TargetAddr":"192.168.127.33:5006",
				"SymRTP":"0",
				"rtcp-mux":"0",
				"TransMode":"sendRecv",
				"pack-mode":"0"
				}
			},

			"id":"1"
		},
		{

			"runctrl":{
				"conf_id":"0_M",
				"chan_id":"0",
				"opt":"start"
			},
			"id":"2"
		}
		]
		#msg[0]['avs_setparam']['audio_transport']['TargetAddr'] = _gvc_media_ipaddress+':'+str(_remote_audio_port)
		#msg[0]['avs_setparam']['audio_transport']['BindPort'] = str(self._bind_audio_port)
		msg[0]['avs_setparam']['video_transport']['TargetAddr'] = _gvc_media_ipaddress+':'+str(_remote_video_port)
		msg[0]['avs_setparam']['video_transport']['BindPort'] = str(self._bind_video_port)
		msg[0]['avs_setparam']['chan_id'] = str(self._channel_number)
		msg[1]['runctrl']['chan_id'] = str(self._channel_number)
		
		msg_json = json.dumps(msg)
		self._conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)		
		response = self._conn.getresponse()
#		response.read()
		print response.status,response.reason,json.dumps(response.read())
		print "Channel:",self._channel_number,"start."
		
	def channelReset(self):    
		headers ={
		"Content-Type":"application/json",
		"Connection":self.connection_type
		}
        
		msg=[{
		"runctrl":{
				"conf_id":"0_M",
				"chan_id":"0",
				'opt':'stop'
			},
		'id':"3"
		},
		{
		"runctrl":{
			"conf_id":"0_M",
			"chan_id":"0",
			'opt':'reset'
			},
			'id':"4"
		}
		]
		msg[0]['runctrl']['chan_id'] = str(self._channel_number)
		msg[1]['runctrl']['chan_id'] = str(self._channel_number)
		msg_json = json.dumps(msg)
		self._conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)
		response = self._conn.getresponse()
#		response.read()
		print response.status,response.reason,json.dumps(response.read())
		print "channel:",self._channel_number,"stop and reset."
  
def main():
	global local_sip_address 
	local_sip_address = sys.argv[1]
	global src_media_address 
	src_media_address = sys.argv[2]
	global local_sip_port 
	local_sip_port = 5060
	media_port = [1]*100
	for i in range(0,100):
		media_port[i] = 10000+i*2
	s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	s.bind((local_sip_address,int(local_sip_port)))
	print sys.argv[0]
	print "Local SIP ipaddress: ",sys.argv[1]
	print "MCU address: ",sys.argv[2]
	#if len(sys.argv) == 1:
	#	print "Usage: sipserver.py [Local_eth0_ipaddress] [MCU_ipaddress]"
	conn = httplib.HTTPConnection(src_media_address,8080)
	channel = 0
	dict = {}
	while 1:
		data,dstaddr=s.recvfrom(2048)
		print "recv", data
		if not data:
			break
		if data[0:8].find("INVITE") == -1 and data[0:8].find("BYE") == -1:
			continue
		if data[0:8].find("INVITE") == 0:
			print "recv invite", data
			dict[dstaddr] = Channel(channel,media_port,data,dstaddr,s,conn)
#			Channel1 = Channel(channel,media_port,data,dstaddr,s,conn)
			dict[dstaddr].response_100()
			dict[dstaddr].response_180()		
			dict[dstaddr].channelStart()
			dict[dstaddr].response_200()
			channel += 1
		if data[0:8].find("BYE") == 0:
			if dict.has_key(dstaddr):
				dict[dstaddr].buffer = data
				dict[dstaddr].response_200_to_BYE()
				dict[dstaddr].channelReset()	
	s.close()

if __name__ == "__main__":
	main();

