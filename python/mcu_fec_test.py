#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import time
import signal
import socket,select
import sys
import os
import dpkt
import struct
import binascii
from threading import Thread

PACKET_SEND_WAIT = 15
MAX_CONF_NUM = 1
MAX_CHAN_NUM = 1
if 1 == MAX_CHAN_NUM:
  PACKET_SEND_WAIT = 1
elif 2 == MAX_CHAN_NUM:
  PACKET_SEND_WAIT = 5
elif 4 == MAX_CHAN_NUM:
  PACKET_SEND_WAIT = 5
elif MAX_CHAN_NUM >= 8:
  PACKET_SEND_WAIT = 5


conn = None
connection_type = 'keep-alive'

def connInit(_conn):
    headers ={
        "Content-Type":"application/json",
        "Connection":connection_type
        }

    msg=[{

        "conninit":{
            "serviceID":"~!@#$%^&*()!@#$%^&*()",
            "recycle":"1"
        },
        "id":"2"
    }
    ]
    
    msg_json = json.dumps(msg)

    _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)

    
    response = _conn.getresponse()
    print response.status,response.reason,json.dumps(response.read())
    
def notifySSRCChanged(_conn):
    headers ={
        "Content-Type":"application/json",
        "Connection":connection_type
        }
        
    msg=[{
        "vdec_ssrc_change":{
            "conf_id":"conference1_M",
            "chan_id":"conference1_chan1",
            "latest_ssrc":"133497297"
        },
        "id":"1"
    }
    ]
    
    msg_json = json.dumps(msg)

    _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)

    
    response = _conn.getresponse()
    print response.status,response.reason,json.dumps(response.read())
        
def channelStart(_conn,_dataSimulation):
    headers ={
        "Content-Type":"application/json",
        "Connection":connection_type
        }

    msg=[{

        "avs_setparam":{
        "conf_id":"0",
        "chan_id":"0",
        "audio_enc_param":{
            "MainCoder":"audio/pcmu",
            "CN":"0",
            "PayloadType":"0",
            "Ptime":"10"
         },
        "audio_dec_param":{
            "Codecs":"audio/pcmu",
            "PayloadType":"0"
            },
        "audio_transport":{
            "BindPort":"5004",
            "TargetAddr":"192.168.127.181:5004",
            "SymRTP":"0",
            "rtcp-mux":"0"
            },
        "video_enc_param":{
            "MainCoder":"video/avc",
            "ImageSize":"640x480",
            "FrameRate":"5",
            "Profile":"HP",
            "BitRate":"450000",
            "PayloadType":"97",
            'PacketizationMode':'1',
            'GopLength':'-1',
            #'FecPT':'120',
            #'FecType':'1',
            'caption':'grandstream潮流网络'
          },
        "video_dec_param":{
            "Codecs":"video/avc",
            "ImageSize":"1920x1080",
            "FrameRate":"15",
            "PayloadType":"107",
            'FecPT':'117',
            'RedPT':'116',
            'FecType':'1',
            'WaitKeyframe':'1'
            },
        "video_transport":{
			"BindPort":"5006",
            "TargetAddr":"192.168.127.181:5006",
            "SymRTP":"0",
            "rtcp-mux":"0",
            "TransMode":"sendRecv",
            "pack-mode":"0",
            "TrafficShaping":"1"
            }
        },
        "id":"1"
    }]
      
    
    msg_runctrl=[ {

        "runctrl":{
            "conf_id":"0",
            "chan_id":"0",
            "opt":"start"
        },
        "id":"2"
    }] 

    for idx,_ in enumerate(_dataSimulation):
        msg[0]['avs_setparam']['conf_id'] = _['conf_id']
        msg[0]['avs_setparam']['chan_id'] = _['chann_id']
        msg[0]['avs_setparam']['video_transport']['BindPort'] = _['dstPortVideo']
        msg[0]['avs_setparam']['video_transport']['TargetAddr'] = _['srcAddrVideo']
        if _.has_key("TransMode") == True:
            msg[0]['avs_setparam']['video_transport']['TransMode'] = _['TransMode']
        msg[0]['avs_setparam']['video_enc_param']['ImageSize'] = _['VencImageSize']
        msg[0]['avs_setparam']['video_enc_param']['BitRate'] = _['BitRate']
        msg[0]['avs_setparam']['video_enc_param']['FrameRate'] = _['FrameRate']
        if _.has_key("VMainCoder") == True:
            msg[0]['avs_setparam']['video_enc_param']['MainCoder'] = _['VMainCoder']    
        if _.has_key("VdecImageSize") == True:
            msg[0]['avs_setparam']['video_dec_param']['ImageSize'] = _['VdecImageSize']
        if _.has_key("VCodecs") == True:
            msg[0]['avs_setparam']['video_dec_param']['Codecs'] = _['VCodecs']
        if _.has_key("VdecFrameRate") == True:
            msg[0]['avs_setparam']['video_dec_param']['FrameRate'] = _['VdecFrameRate']
        msg[0]['avs_setparam']['audio_transport']['BindPort'] = _['dstPortAudio']
        msg[0]['avs_setparam']['audio_transport']['TargetAddr'] = _['srcAddrAudio']

        if _.has_key("TrafficShaping") == True:
            msg[0]['avs_setparam']['video_transport']['TrafficShaping'] = _['TrafficShaping']

        if _.has_key("PTransMode") == True:
            msg[0]['avs_setparam']['content_transport']['TransMode'] = _['PTransMode']
            msg[0]['avs_setparam']['content_transport']['BindPort'] = _['dstPortContent']
            msg[0]['avs_setparam']['content_transport']['TargetAddr'] = _['srcAddrContent']
            if _.has_key("PMainCoder") == True:
                msg[0]['avs_setparam']['content_enc_param']['MainCoder'] = _['PMainCoder']    
            if _.has_key("PCodecs") == True:
                msg[0]['avs_setparam']['content_dec_param']['Codecs'] = _['PCodecs']
        else:
            if msg[0]['avs_setparam'].has_key("content_enc_param") == True:
                del msg[0]['avs_setparam']['content_enc_param']
                del msg[0]['avs_setparam']['content_dec_param']
                del msg[0]['avs_setparam']['content_transport']

        #msg[1]['runctrl']['conf_id'] = _['conf_id']
        #msg[1]['runctrl']['chan_id'] = _['chann_id']

        #msg[2]['runctrl']['conf_id'] = _['conf_id']
        #msg[2]['runctrl']['chan_id'] = _['chann_id']

        msg_json = json.dumps(msg)

        _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)

        
        tm1 = time.time()
        response = _conn.getresponse()
        print response.status,response.reason,json.dumps(response.read())
        tm2 = time.time()
        intv= int((tm2 - tm1)*1000)
        if intv > 200:
            print 'setparamter',intv



        msg_runctrl[0]['runctrl']['conf_id'] = _['conf_id']
        msg_runctrl[0]['runctrl']['chan_id'] = _['chann_id']

        #msg[2]['runctrl']['conf_id'] = _['conf_id']
        #msg[2]['runctrl']['chan_id'] = _['chann_id']

        msg_json = json.dumps(msg_runctrl)
        _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)

        tm1 = time.time()
        response = _conn.getresponse()
        print response.status,response.reason,json.dumps(response.read())
        tm2 = time.time()
        intv= int((tm2 - tm1)*1000)
        if intv > 200:
            print 'start',intv

        msg_vdec_limit=[ {
            "vdec_capacity_limit":{
                 "conf_id":"0",
                 "chan_id":"0",
                 "max_width":"1280",
                 "max_height":"720",
            },
            "id":"2"
        }] 
        msg_vdec_limit[0]['vdec_capacity_limit']['conf_id'] = _['conf_id']
        msg_vdec_limit[0]['vdec_capacity_limit']['chan_id'] = _['chann_id']

        #msg[2]['runctrl']['conf_id'] = _['conf_id']
        #msg[2]['runctrl']['chan_id'] = _['chann_id']

        msg_json = json.dumps(msg_vdec_limit)

        #_conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)
        #response = _conn.getresponse()
        #print response.status,response.reason,json.dumps(response.read())

        msg_caption=[ {
            "mix_text_param":{
                 "conf_id":"0",
                 "chan_id":"0",
                 "mix_text":"~!@#$%^&*(){}:;,.<>|\\/\"\'潮流网络grandstream多媒体技术部杭研所深圳市潮流网络技术有限公司"
            },
            "id":"2"
        }] 
        msg_caption[0]['mix_text_param']['conf_id'] = _['conf_id']
        msg_caption[0]['mix_text_param']['chan_id'] = _['chann_id']

        #msg[2]['runctrl']['conf_id'] = _['conf_id']
        #msg[2]['runctrl']['chan_id'] = _['chann_id']

        msg_json = json.dumps(msg_caption)

        _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)
        response = _conn.getresponse()
        print response.status,response.reason,json.dumps(response.read())

def channelReset(_conn,_dataSimulation):    
    headers ={
        "Content-Type":"application/json",
        "Connection":connection_type
        }
        
    msg=[{
        "runctrl":{
                "conf_id":"0",
                "chan_id":"0",
                'opt':'stop_content'
            },
        'id':"5"
        },{
        "runctrl":{
                "conf_id":"0",
                "chan_id":"0",
                'opt':'stop'
            },
        'id':"3"
        },
        {
        "runctrl":{
            "conf_id":"0",
            "chan_id":"0",
            'opt':'reset'
            },
            'id':"4"
        }
        ]
         
    
    for idx,_ in enumerate(_dataSimulation):  
        msg[0]['runctrl']['conf_id'] = _['conf_id']
        msg[0]['runctrl']['chan_id'] = _['chann_id']

        msg[1]['runctrl']['conf_id'] = _['conf_id']
        msg[1]['runctrl']['chan_id'] = _['chann_id']

        msg[2]['runctrl']['conf_id'] = _['conf_id']
        msg[2]['runctrl']['chan_id'] = _['chann_id']

        msg_json = json.dumps(msg)

        _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)

        tm1 = time.time()
        response = _conn.getresponse()
        print response.status,response.reason,json.dumps(response.read())
        tm2 = time.time()
        intv= int((tm2 - tm1)*1000)
        if intv > 200:
            print 'reset',intv

def avsexit(_conn): 
    headers ={
        "Content-Type":"application/json",
        "Connection":connection_type
        }
        
    msg=[{
        "runctrl":{
                "conf_id":"0",
                "chan_id":"0",
                'opt':'exit'
            },
        'id':"3"
        }
        ]


    msg_json = json.dumps(msg)

    _conn.request('POST','/com/grandstream/httpjson/avs',msg_json,headers)
    response = _conn.getresponse()
    print response.status,response.reason,json.dumps(response.read())

class ThreadMediaSend(Thread):
    def __init__(self, _pcapFile,_addr,_port):
        ''' Constructor. '''
 
        Thread.__init__(self)

        self.pcapFile = _pcapFile
        print "self pcap File :%s"%(_pcapFile)
        self.addr = _addr
        self.port = _port
        self.runable = True
      
    def stop(self):
        self.runable = False  
 
    def run(self):
        #f = open(self.pcapFile)
        time.sleep(3)
        #pcap = dpkt.pcap.Reader(f)
        h264pt=[96,97,99,107,105,109]

        sock = socket.socket(socket.AF_INET, # Internet
                                socket.SOCK_DGRAM) # UDP

        sock_rtcp = socket.socket(socket.AF_INET, # Internet
                                socket.SOCK_DGRAM) # UDP
        _ts = -1;
        fir_seq =0
        repeatcount = 0
        keepalive_ts = -1
        packet_count = 0
        rtpseq = -1
        ssrc_prev = -1
        while 1:
            if not self.runable:
                break

            f = open(self.pcapFile)
            pcap = dpkt.pcap.Reader(f)
            for ts, buf in pcap:
                if not self.runable:
                    break

                if pcap.dloff == 14:
                   eth = dpkt.ethernet.Ethernet(buf)
                elif pcap.dloff == 16:
                   eth = dpkt.sll.SLL(buf)
                else:
                  print pcap.dloff,'is unknown'
                #print eth.data.__class__.__name__,ts
                
                if eth.data.__class__.__name__=='IP':
                    ip = eth.data
                    if ip.data.__class__.__name__=='UDP':
                        udp = ip.data
                        try:
                            rtp = dpkt.rtp.RTP(udp.data)
                            if False:#(rtp.seq >= 24304 and rtp.seq <=24317 and rtp.pt == 120):
                                print "miss seq %d"%(rtp.seq)
                                continue
                                #if rtpseq == -1:
                                #   pass
                                #elif (rtpseq +1) != rtp.seq:
                                #   print '!!!!!!!!!!  rtp cur seq:%d  pre seq:%d !!!!!!!!!!!!!!'%(rtp.seq, rtpseq)
                                #if (ord(rtp.data[0]) & 0x7f) == 107:
                                #    pack_file = open('send/'+str(rtp.seq) + '.pack', 'w')
                                #    pack_file.write(rtp.data[1:])
                                #    pack_file.close();
                            if ssrc_prev == -1:
                                ssrc_prev = rtp.ssrc
                            elif ssrc_prev != rtp.ssrc:
                                conn = httplib.HTTPConnection("192.168.121.92",8080)
                                notifySSRCChanged(conn)
                                conn.close()
                                print "ssrc_prev %d, rtp.ssrc %d rtp.seq %d"%(ssrc_prev, rtp.ssrc, rtp.seq)
                                ssrc_prev = rtp.ssrc
                                time.sleep(1)
                                print "sleep 1s"                    
                            rtpseq = rtp.seq
                            if rtpseq == 21224:
								print "rtpseq == 21224"
                            sock.sendto(udp.data, (self.addr, int(self.port)))
                            if _ts == -1:
                                _ts = ts;
                                keepalive_ts = time.time()
                            else:
                                if int((ts - _ts)*10000) > PACKET_SEND_WAIT :
                                   if (ts -_ts) > 100: 
                                       time.sleep(1)
                                   else: 
                                       time.sleep(float(int((ts - _ts)*10000))/10000)
                                #time.sleep( ts - _ts)
                                _ts = ts

                                packet_count = packet_count + 1
                                
                            if  int(time.time() - keepalive_ts) > 5:
                                data = struct.pack('BBBBBBBBBBBB', 0x40, 0x00, 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00);
                                sock.sendto(data, (self.addr, int(self.port)))
                                keepalive_ts = time.time()
                                

                                data_rtcp = struct.pack('BBBBBBBBBBBBBBBBBBBB', 0x84, 206, 0x00,4,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x12,0x34,0x56,0x78,fir_seq,0,0,0);
                                fir_seq = fir_seq + 1
                                if fir_seq > 255:
                                    fir_seq = 0
                                #sock_rtcp.sendto(data_rtcp, (self.addr, int(self.port)+1))
                                print "keep time %d"%(keepalive_ts)
                                

                          
                        except dpkt.dpkt.NeedData:
                            continue
                        except dpkt.dpkt.UnpackError:
                            continue

            repeatcount = repeatcount + 1
            f.close()
            break
            #if repeatcount > 3:
            #    break
        print "send finish !"
        sock_rtcp.close()
        sock.close()
        f.close()

class ThreadMediaRecv(Thread):
    def __init__(self, _outfile,_addr,_port):
        ''' Constructor. '''
 
        Thread.__init__(self)

        self.outfileVideo = _outfile
        self.addr = _addr
        self.port = _port
        self.runable = True 

    def stop (self):
        self.runable = False

    def run(self):
        rtpseq = -1
        nalhead=0x00000001
        fd_out= open(self.outfileVideo,'w')

        h264pt=[96,97,99,107,105,109,102,101]

        sock = socket.socket(socket.AF_INET, # Internet
                                socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.addr, int(self.port)))

        while self.runable:
            infds,outfds,errfds = select.select([sock,],[],[],0.1)
            if len(infds) != 0 and (sock in infds):
                _data,_srcaddr=sock.recvfrom(1500)
                #print len(_data),_srcaddr

                rtp = dpkt.rtp.RTP(_data)
                #print rtp.pt

                '''
                todo:丢包  乱序 
                '''
                if rtp.pt in h264pt :#and '192.168.122.154' == srcipaddr:
                    #print rtp.seq,rtpseq
                    if rtpseq == -1:
                       pass
                    elif (rtpseq +1) != rtp.seq:
                       print '!!!!!!!!!!  rtp cur seq:%d  pre seq:%d !!!!!!!!!!!!!!'%(rtp.seq, rtpseq)


                    rtpseq = rtp.seq
                    #print 'rtpseq %d'%rtpseq

                    try:
                        F=(ord(rtp.data[0])>>7)&0x1
                        NRI=(ord(rtp.data[0])>>5)&0x3
                        TYPE=ord(rtp.data[0])&0x1F

                        firstkeyframe = 1
                        #print 'TYPE %d'%TYPE
                        if TYPE==28:#FU-A

                            S=(ord(rtp.data[1])>>7)&0x1
                            E=(ord(rtp.data[1])>>6)&0x1
                            R=(ord(rtp.data[1])>>5)&0x1
                            NALTYPE=(ord(rtp.data[0]) & 0xe0) | (ord(rtp.data[1] )& 0x1f)
                            # print S,E,R,hex(NALTYPE)
                            if S == 1:
                                fd_out.write(struct.pack('!I',nalhead))


                                fd_out.write(struct.pack('B',int(NALTYPE)))

                                fd_out.write(rtp.data[2:])
                                #print binascii.b2a_hex(rtp.data[:10])
                                pass
                            else:
                                fd_out.write(rtp.data[2:])
                                pass
                        elif TYPE == 24: #STAP-A
                            datalen = len(rtp.data)
                            #print 'stap-a len:%d-------------'%datalen

                            datalen = datalen - 1

                            offset = 1
                            while datalen >= 2:

                                nalSize = (ord(rtp.data[offset]) << 8) | ord(rtp.data[offset+1]);
                                #print 'nalSize len:%d %d'%(nalSize,datalen)
                                if datalen < nalSize + 2 :
                                    print 'Discarding malformed STAP-A packet'
                                    break;
                                fd_out.write(struct.pack('!I',nalhead))
                                fd_out.write(rtp.data[offset+2:offset+2+nalSize])
                                #print binascii.b2a_hex(rtp.data[offset+2:offset+2+1])

                                offset += 2 + nalSize;
                                datalen -= 2 + nalSize;

                        else:
                            #print hex(ord(rtp.data[0]) )
                            fd_out.write(struct.pack('!I',nalhead))
                            #print binascii.b2a_hex(rtp.data[0:1])
                            fd_out.write(rtp.data)
                            pass
                    except:
                            continue
                elif rtp.pt in [0]: #pcmu
                    fd_out.write(rtp.data)
                    pass
                else:
                    print 'pt:%d unknow'%rtp.pt

        sock.close()
        fd_out.close()

mediaSendThread_video = []
mediaRecvThread_video = []

mediaSendThread_content = []
mediaRecvThread_content = []

mediaSendThread_audio = []
mediaRecvThread_audio = []
mediaRecvThread_vp8_video = []

class ThreadMediaRecvVP8(Thread):
    def __init__(self, _outfile,_addr,_port):
        ''' Constructor. '''
 
        Thread.__init__(self)

        self.outfileVideo = _outfile
        self.addr = _addr
        self.port = _port
        self.runable = True 

        
    def writeIVFHead(self, _outfile, _framecnt):
        headFlg=struct.pack('cccc', 'D', 'K', 'I', 'F')
        _outfile.write(headFlg)
        version=struct.pack('H', 0x0);
        _outfile.write(version)
        headSize=struct.pack('H', 32)
        _outfile.write(headSize)
        fourcc=struct.pack('I', 0x30385056);
        _outfile.write(fourcc)
        width=struct.pack('BB', 0x80, 0x07);
        _outfile.write(width)
        height=struct.pack('BB', 0x38, 0x04);
        _outfile.write(height)
        den=struct.pack('I', 0x1);
        _outfile.write(den)
        num=struct.pack('I', 10000);
        _outfile.write(num)
        framecnt=struct.pack('I', 0xFFFFFFFF);
        _outfile.write(framecnt)
        unused=struct.pack('I', 0x0);
        _outfile.write(unused)

        
    def writeFrameHead(self, _outfile, _framesize, _pts):
        head=[0]*12
        frameSize = struct.pack('I', _framesize);
        _outfile.write(frameSize)
        PTS = struct.pack('Q', _pts);
        _outfile.write(PTS)

        
    def stop (self):
        self.runable = False

    def run(self):
        nalhead=0x00000001
        fd_out= open(self.outfileVideo,'w')

        headFlg=struct.pack('cccc', 'D', 'K', 'I', 'F')
        fd_out.write(headFlg)
        version=struct.pack('H', 0x0);
        fd_out.write(version)
        headSize=struct.pack('H', 32)
        fd_out.write(headSize)
        fourcc=struct.pack('I', 0x30385056);
        fd_out.write(fourcc)
        width=struct.pack('BB', 0x80, 0x07);
        fd_out.write(width)
        height=struct.pack('BB', 0x38, 0x04);
        fd_out.write(height)
        den=struct.pack('I', 90000);
        fd_out.write(den)
        num=struct.pack('I', 0x1);
        fd_out.write(num)
        framecnt=struct.pack('I', 0xFFFFFFFF);
        fd_out.write(framecnt)
        unused=struct.pack('I', 0x0);
        fd_out.write(unused)

        vp8pt=[96,97,99,107,105,109,102,101]

        sock = socket.socket(socket.AF_INET, # Internet
                                socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.addr, int(self.port)))
        frameSz=0
        seekPos = 32;
        packetSz=0;
        framecnt = 0;
        firstFrame=True
        unFinishLen=0;
        while self.runable:

            infds,outfds,errfds = select.select([sock,],[],[],0.1)
            if len(infds) != 0 and (sock in infds):
                _data,_srcaddr=sock.recvfrom(1500)
                #print len(_data),_srcaddr

                rtp = dpkt.rtp.RTP(_data)
                #print rtp.pt
  

                '''
                todo:丢包  乱序 
                '''
                if rtp.pt in vp8pt :#and '192.168.122.154' == srcipaddr:
                    #print rtp.seq,rtpseq
                    #if rtpseq == -1:
                    #   pass
                    #elif (rtpseq +1) != rtp.seq:
                    #   print '!!!!!!!!!!  rtp cur seq:%d  pre seq:%d !!!!!!!!!!!!!!'%(rtp.seq, rtpseq)


                    rtpseq = rtp.seq
                    #print 'rtpseq %d'%rtpseq

                    try:
                        offset=0;
                        X=(ord(rtp.data[0])&0x80)
                        S=(ord(rtp.data[0])&0x10)
                        PartID=(ord(rtp.data[0])&0xF)
                        offset+=1
                        if PartID > 8 :
                                break;
                        
                        if X:
                            I=(ord(rtp.data[1])&0x80)
                            L=(ord(rtp.data[1])&0x40)
                            T=(ord(rtp.data[1])&0x20)
                            K=(ord(rtp.data[1])&0x10)
                            offset+=1
                            if I:
                                pictureId=(ord(rtp.data[2])&0x7F)
                                offset+=1
                                if ord(rtp.data[2]) & 0x80 :
                                    pictureId=(pictureId<<8)+ord(rtp.data[3])
                                    offset+=1
                            if L:
                                offset+=1
                            if T or K:
                                offset+=1

                        if S and firstFrame : #begin of partition
                            firstFrame = False
                            framecnt+=1;
                        elif S :
                            seekPos +=(frameSz+12);
                            frameSz = 0;
                            unFinishLen = 0;
                            framecnt+=1;
                            #print 'new seek pos %d'%seekPos

                        packetSz=len(rtp.data) - offset
                        frameSz += packetSz                        
                        fd_out.seek(seekPos)
                        #print 'seekPos %d'%seekPos
                        frameSize = struct.pack('I', frameSz);
                        fd_out.write(frameSize)
                        PTS = struct.pack('Q', rtp.ts);
                        fd_out.write(PTS)
                        
                        fd_out.seek(unFinishLen+12+seekPos);


                        unFinishLen +=packetSz;

                        


                        fd_out.write(rtp.data[offset:])

                        
                        pos=fd_out.tell();
                        fd_out.seek(24)
                        frameNo = struct.pack('I', framecnt);
                        fd_out.write(frameNo);
                        fd_out.seek(pos)

                    except:
                            continue
                elif rtp.pt in [0]: #pcmu
                    fd_out.write(rtp.data)
                    pass
                else:
                    print 'pt:%d unknow'%rtp.pt
                    
        fd_out.seek(32)
        #writeIVFHead(fd_out, frameNo)
        sock.close()
        fd_out.close()

def doMediaSendRecv (_conn, _dataSimulation):
    global mediaSendThread_video
    global mediaRecvThread_video

    global mediaSendThread_content
    global mediaRecvThread_content

    global mediaSendThread_audio
    global mediaRecvThread_audio
    global mediaRecvThread_vp8_video

    mediaSendThread_video = []
    mediaRecvThread_video = []
    mediaRecvThread_vp8_video = []

    mediaSendThread_content = []
    mediaRecvThread_content = []

    mediaSendThread_audio = []
    mediaRecvThread_audio = []

    for idx,_ in enumerate(_dataSimulation):
        try:

            if _.has_key("VMainCoder") == True and cmp(_["VMainCoder"], "video/vp8") == 0:
                    mediaRecvThread_video.append(ThreadMediaRecvVP8(_['outfileVP8Viode'],_['srcAddrVideo'].split(':')[0],_['srcAddrVideo'].split(':')[1])) 
            else :
                mediaRecvThread_video.append(ThreadMediaRecv(_['outfileVideo'],_['srcAddrVideo'].split(':')[0],_['srcAddrVideo'].split(':')[1]))
        
            mediaRecvThread_video[idx].setName(_['chann_id'])

            mediaRecvThread_video[idx].start()
            
            ################################################################################################################################
            '''
            mediaRecvThread_audio.append(ThreadMediaRecv(_['outfileAudio'],_['srcAddrAudio'].split(':')[0],_['srcAddrAudio'].split(':')[1]))
            mediaRecvThread_audio[idx].setName(_['chann_id'])
            mediaRecvThread_audio[idx].start()
            '''
            
            ##################################################################################################################################

            if _.has_key("PTransMode") == True and cmp(_["PTransMode"], "sendOnly") == 0:
                if cmp(_["PMainCoder"], "video/vp8") == 0:
                    mediaRecvThread_content.append(ThreadMediaRecvVP8(_['outfileContent'],_['srcAddrContent'].split(':')[0],_['srcAddrContent'].split(':')[1])) 
                else:
                    mediaRecvThread_content.append(ThreadMediaRecv(_['outfileContent'],_['srcAddrContent'].split(':')[0],_['srcAddrContent'].split(':')[1])) 
                mediaRecvThread_content[len(mediaRecvThread_content) - 1].setName(_['chann_id'])
                mediaRecvThread_content[len(mediaRecvThread_content) - 1].start()

        except Exception, e:
            print e
    
    for idx,_ in enumerate(_dataSimulation):
        try:
            ###########################################################################
            #     send video stream thread when TransMode is not sendOnly
            ###########################################################################
            if _.has_key("TransMode") == True :#and cmp(_["TransMode"], "sendOnly"):
                mediaSendThread_video.append(ThreadMediaSend(_['videopcap'],_['dstAddr'],_['dstPortVideo']))
                mediaSendThread_video[len(mediaSendThread_video) -1].setName(_['chann_id'])
                mediaSendThread_video[len(mediaSendThread_video) -1].start()
            else:
                print 'mediaSendThread_video %s without start '%(_['chann_id'])

            ###########################################################################
            #     send audio stream thread 
            ###########################################################################
            '''
            mediaSendThread_audio.append(ThreadMediaSend(_['audiopcap'],_['dstAddr'],_['dstPortAudio']))
            mediaSendThread_audio[len(mediaSendThread_audio) -1].setName(_['chann_id'])
            mediaSendThread_audio[len(mediaSendThread_audio) -1].start()
            '''

            ###########################################################################
            #   start  send content stream thread when PTransMode is recvOnly 
            ###########################################################################
            if _.has_key("PTransMode") == True and cmp(_["PTransMode"], "recvOnly") == 0:
                mediaSendThread_content.append(ThreadMediaSend(_['contentcap'],_['dstAddr'],_['dstPortContent']))
                mediaSendThread_content[len(mediaSendThread_content) -1].setName(_['chann_id'])
                mediaSendThread_content[len(mediaSendThread_content) -1].start()
            else:
                print 'mediaSendThread_content %s without start '%(_['chann_id'])


        except Exception, e:
            print e


def doMediaSendRecv_join (_conn, _dataSimulation):

    for _ in mediaSendThread_video:
        _.join()
    for _ in mediaSendThread_audio:
        _.join()
    for _ in mediaSendThread_content:
        _.join()

    for _ in mediaRecvThread_video:
        _.stop()
    for _ in mediaRecvThread_audio:
        _.stop()
    for _ in mediaRecvThread_vp8_video:
        _.stop()
    for _ in mediaRecvThread_content:
        _.stop()

    for _ in mediaRecvThread_video:
        _.join()
    for _ in mediaRecvThread_audio:
        _.join()
    for _ in mediaRecvThread_vp8_video:
        _.join()
    for _ in mediaRecvThread_content:
        _.join()

def doMediaSendRecv_stop(_conn, _dataSimulation):
    global mediaSendThread_video
    global mediaSendThread_content
    global mediaSendThread_audio
    global mediaRecvThread_video
    global mediaRecvThread_vp8_video
    global mediaRecvThread_content
    global mediaRecvThread_audio

    for _ in mediaSendThread_video:
        _.stop()
    for _ in mediaSendThread_content:
        _.stop()
    for _ in mediaSendThread_audio:
        _.stop()

    for _ in mediaRecvThread_video:
        _.stop()
    for _ in mediaRecvThread_audio:
        _.stop()
    for _ in mediaRecvThread_vp8_video:
        _.stop()
    for _ in mediaRecvThread_content:
        _.stop()
    
    


def create_testParameter (_parameter):

    _resolution_map={1:'1920x1080',2:'1920x1072',3:'1920x1088'}

    for _confId in range(1,MAX_CONF_NUM+1) :
        for  _chanId in range(1,MAX_CHAN_NUM+1):
            
            _ = {}
            _['conf_id'] = 'conference'+str(_confId)+'_M'
            _['chann_id'] = 'conference'+str(_confId)+'_chan'+str(_chanId)
            _['audiopcap'] = 'audio_0.pcap'

            if 1 == MAX_CHAN_NUM:
                 _['videopcap'] = 'clock.pcap'#''ssrc_changed.pcap'#'hybird_ssrc.pcap'#'720p_15fps_avc.pcap'#'recv_miss%5.pcap'
                 #_['videopcap'] = '720p_15fps_avc.pcap'#'vga_15fps_vp8.pcap'#'720p_15fps_vp8.pcap' #'h264_res.pcap' #'vp8res.pcap' #'720p_15fps_vp8.pcap'  #'720p_15fps_avc.pcap' 
                 _['VdecImageSize'] = '1920x1080'
            elif 2 == MAX_CHAN_NUM:
                 _['videopcap'] = '720p_15fps_avc.pcap'
                 _['VdecImageSize'] = '1280x720'
            elif  MAX_CHAN_NUM <= 4 :
           	 #_['videopcap'] = '1080p_15fps.pcap' #'h264_res.pcap'  #'720p_15fps_avc.pcap' 
           	 _['videopcap'] = '720p_15fps_avc.pcap' #'h264_res.pcap' #'vp8res.pcap' #'720p_15fps_vp8.pcap'  #'720p_15fps_avc.pcap' 
                 #_['videopcap'] = 'ak_send_to_mcu_rtp_and_fec_46650.pcap'
                 _['VdecImageSize'] = '1280x720'
            elif MAX_CHAN_NUM <= 9:
           	 _['videopcap'] = 'vga_15fps_avc.pcap'#'VGA_res_avc_1min.pcap'
                 _['VdecImageSize'] = '640x480'
            else:
           	 _['videopcap'] = '1080p_15fps.pcap' 

            _['dstAddr'] = '192.168.121.92'
            _['dstPortAudio'] = str(60000+100*_confId + _chanId*2+(_chanId-1)*2)
            _['dstPortVideo'] = str(60000+100*_confId + (_chanId+1)*2+(_chanId-1)*2)
            _['VencImageSize'] =  _resolution_map[1]
            _['BitRate'] = str(1024*1024) #str(512*1024*_confId)
            _['FrameRate'] = '15'
            _['VdecFrameRate'] = '15'
            _['outfileVideo'] = 'conf'+str(_confId)+'_chan'+str(_chanId)+'.h264'
            _['outfileAudio'] = 'conf'+str(_confId)+'_chan'+str(_chanId)+'.pcmu'
            _['srcAddrAudio'] = '192.168.127.181:'+_['dstPortAudio']
            _['srcAddrVideo'] = '192.168.127.181:'+_['dstPortVideo']
            _['TransMode'] = 'recvOnly'
            _['VMainCoder'] = 'video/avc'
            '''
            # old conf
            if _chanId == 1:
              _['TransMode'] = 'sendRecv'
              
              _['VencImageSize'] = '1920x1080'
              _['BitRate'] = str(1024*1024) 
              pass
            elif _chanId == 2:
              _['TransMode'] = 'recvOnly'
              _['VencImageSize'] = '1280x720'
              _['BitRate'] = str(1536*1024) 
              pass
            elif _chanId == 3:
              _['TransMode'] = 'recvOnly'
              _['VencImageSize'] = '848x480'
              _['BitRate'] = str(1024*1024) 
              pass
            elif _chanId == 4:
              _['TransMode'] = 'sendRecv'
              _['VencImageSize'] = '1920x1080'
              _['BitRate'] = str(1024*1024) 
              _['VMainCoder'] = 'video/vp8'
              pass
           '''
      
            # new conf.
            
            if _chanId == 1:
              _['TransMode'] = 'sendRecv'
              _['VencImageSize'] = '640x480'#'1920x1080'
              _['BitRate'] = str(1024*1024) 
              pass
            elif _chanId == 2:
              _['TransMode'] = 'sendRecv'
              _['VencImageSize'] = '1280x720'
              _['BitRate'] = str(1024*1024) 
              pass
            elif _chanId == 3:
              _['TransMode'] = 'sendRecv'
              _['VencImageSize'] = '848x480'
              _['BitRate'] = str(512*1024) 
              pass
            elif _chanId == 4:
              _['TransMode'] = 'sendRecv'
              _['VencImageSize'] = '1280x720'
              _['BitRate'] = str(1024*1024) 
              _['VMainCoder'] = 'video/vp8'
              pass
            

            _['VCodecs'] = 'video/avc'
            _['outfileVP8Viode'] = 'conf'+str(_confId)+'_chan'+str(_chanId)+'.ivf'




            _parameter.append(_)

    '''
    for _confId in range(1,MAX_CONF_NUM+1) :
        for  _chanId in range(1,3):
            _ = {}
            _['conf_id'] = 'conference'+str(_confId)+'_S'
            _['chann_id'] = 'conference'+str(_confId)+'_chan'+str(_chanId)
            _['audiopcap'] = 'audio_0.pcap'
            _['videopcap'] = '1080p_5fps_avc.pcap'#'S_mcu_receive_54664_h264.pcap'#'1080p_5fps_avc.pcap'   #'h264_res.pcap' #'vp8res.pcap' #'1080p_5fps_avc.pcap'
            _['dstAddr'] = '192.168.121.92'
            _['dstPortAudio'] = str(20000+100*_confId + _chanId*2+(_chanId-1)*2)
            _['dstPortVideo'] = str(20000+100*_confId + (_chanId+1)*2+(_chanId-1)*2)
            _['VencImageSize'] = _resolution_map[1]
            _['BitRate'] = str(512*1024*_confId)
            _['FrameRate'] = '5'
            _['VdecFrameRate'] = '5'
            _['VdecImageSize'] = '1920x1080'
            _['outfileVideo'] = 'confS'+str(_confId)+'_chan'+str(_chanId)+'.h264'
            _['outfileAudio'] = 'confS'+str(_confId)+'_chan'+str(_chanId)+'.pcmu'
            _['srcAddrAudio'] = '192.168.127.181:'+_['dstPortAudio']
            _['srcAddrVideo'] = '192.168.127.181:'+_['dstPortVideo']
            _['TransMode'] = 'sendRecv'
            _['VMainCoder'] = 'video/avc'
            #_['TrafficShaping'] = '1'

            if _chanId > 1:
                _['TransMode'] = 'sendOnly'
                _['VMainCoder'] = 'video/vp8'

            _['VCodecs'] = 'video/avc'
            _['outfileVP8Viode'] = 'confS'+str(_confId)+'_chan'+str(_chanId)+'.ivf'




            _parameter.append(_)
    '''
_dataParamter = []
def signalHandler(signalNo, arg2):
    print "receive signal SIGINT, killed",signalNo, arg2
    global _dataParamter

    conn = httplib.HTTPConnection("192.168.121.92",8080)
    channelReset(conn,_dataParamter)
    doMediaSendRecv_stop(conn, _dataParamter)
    os._exit(0)

def main():  
    try:
        conn = 0
        # _dataParamter = []
        global _dataParamter

        create_testParameter(_dataParamter)
        #conn.set_debuglevel(255)
        signal.signal(signal.SIGINT, signalHandler)
        count = 0
        print conn
        #connInit(conn)

        #return
        limitCount = int(sys.argv[1])
        while count < limitCount:
            print('limitCount:%d'%limitCount)
            conn = httplib.HTTPConnection("192.168.121.92",8080)
            doMediaSendRecv(conn,_dataParamter)
            channelStart(conn,_dataParamter)
            conn.close()

            time.sleep(1000000)
            doMediaSendRecv_join(conn,_dataParamter)
            # time.sleep(20)

            conn = httplib.HTTPConnection("192.168.121.92",8080)
            channelReset(conn,_dataParamter)
            doMediaSendRecv_stop(conn, _dataParamter)
            #time.sleep(0.1)
            count = count +1
            print('------------------test count:%d---------------------'%count)
            # time.sleep(10)
        #if len(sys.argv) == 3:
        #    avsexit(conn)
    except Exception, e:
        print '---'
        print e
    finally:
        if conn:
            conn.close()
if __name__ == "__main__":  
    main();



