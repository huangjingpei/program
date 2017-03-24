#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 2017年 01月 22日 星期日 09:44:10 CST
# parse pcap packet: rtp payload for h264/vp8.
# usage: ./videoAssemble4pcap.py -i pcapfilename -o outname -p pt -c codec          or ./videoAssemble4pcap.py -i pcapfilename. default outname is             pcapfilename.h264 remove .pcap; pt is 97; codec is h264.

import math 
import sys
import dpkt
import struct
import binascii
import StringIO
import getopt
import logging  
from logging.handlers import TimedRotatingFileHandler,RotatingFileHandler

class BitReader():
    def __init__(self, byte_stream):
        self.bytes = byte_stream
        self.current_num = 0
        self.available_bits = 0
    def bytes_to_num(self, bytes):
        l = len(bytes)
        acc = 0
        for byte in bytes:
            acc += ord(byte)*256**(l-1)
            l -= 1
        return acc
    def maybe_read_more(self, n):
        if self.available_bits < n:
            more_bytes = int(math.ceil((n-self.available_bits)/8.0))
            new_bytes = self.bytes.read(more_bytes)
            if new_bytes == '':
                raise Exception("Insufficient bits")
            self.current_num = 256**more_bytes*self.current_num
            self.current_num += self.bytes_to_num(new_bytes)
            self.available_bits += 8*more_bytes

    def read_bits(self, n):
        self.maybe_read_more(n)
        ones_mask = 2**self.available_bits-1
        low_bits = 2**(self.available_bits-n) - 1
        high_bits = ones_mask - low_bits
        nbits = self.current_num & high_bits
        self.current_num -= nbits
        nbits = nbits >> (self.available_bits - n)
        self.available_bits -= n
        return nbits

    def read_ugolomb(self):
        def consume_zeros():
            """ Will read up to, and including the next 1 """
            bit = self.read_bits(1)
            count = 0
            while bit == 0:
                count += 1
                bit = self.read_bits(1)
            return count
        try:
            zeros = consume_zeros()
        except:
            raise Exception("Invalid Golomb Code: No 1's found")
        try:
            num = 2**(zeros) + self.read_bits(zeros) - 1
        except Exception as e:
            raise Exception("Invalid Golomb code: Insufficient bits after leading zeros")
        return num
    def read_sgolomb(self):
        golomb = self.read_ugolomb()
        if golomb % 2 == 0:
            return (golomb / 2) * -1
        return (golomb+1) / 2

class Assembler():
    def __init__(self,outfilename,logger):
        self.logger = logger
        self.outfilename = outfilename
        self.fdout = open(outfilename,'w')

        self.logger.info('open %s ok!',outfilename)

    def __del__(self):
        self.fdout.close()
        print '%s output finish!'%self.outfilename

    def packetAssemble(self,rtp):
        print "Assembler.packetAssemble()"  
        pass 

class H264Assembler(Assembler):
    def __init__(self,outfilename,logger):
        Assembler.__init__(self,outfilename,logger)
        self.skipcnt = 0
        self.firstkeyframe = 0
        self.nalhead=0x00000001
        self.width = 0
        self.height = 0
        self.profile = ''
        self.levelid = 0


    # reference doc https://en.wikipedia.org/wiki/H.264/MPEG-4_AVC
    def profile_idc_int_to_str(self,profile_idc):
        profile_idc_str = ""
        if profile_idc == 66:
          profile_idc_str = "Baseline"
        elif profile_idc == 77:
          profile_idc_str = "Main"
        elif profile_idc == 88:
          profile_idc_str = "Extended"
        elif profile_idc == 100:
          profile_idc_str = "High(FRExt)"
        elif profile_idc == 110:
          profile_idc_str = "High10(FRExt)"
        elif profile_idc == 122:
          profile_idc_str = "High4:2:2(FRExt)"
        elif profile_idc == 144:
          profile_idc_str = "High4:4:4(FRExt)"

        return profile_idc_str


    def scaling_list(self,scalingList, sizeOfScalingList, useDefaultScalingMatrixFlag):
      '''ffmpeg和avs中对此处处理稍有区别，在此处理效果有待测试。
         ffmpeg处理函数：decode_scaling_matrices
             和h264-2012标准稍有差别，有待详解
         avs处理函数：InterpretSPS--Scaling_List
             和h264-2012标准接近，但ZZ_SCAN和ZZ_SCAN8与规定中不是太吻合
      '''
      global bitdata
      lastScale = 8
      nextScale = 8

      for j in range(sizeOfScalingList):
        if nextScale != 0:
          delta_scale = bitdata.read_sgolomb()
          nextScale = ( lastScale + delta_scale + 256 ) % 256
          useDefaultScalingMatrixFlag = (j == 0 and nextScale == 0)

        scalingList[j] = (nextScale == 0) and lastScale or nextScale

        lastScale = scalingList[j]


    # reference doc http://www.itu.int/ITU-T/recommendations/rec.aspx?rec=11466&lang=zh
    def read_sequence_paramter_set(self,data):
      'parse h264 sps'
      global bitdata
      '''
      default_scaling4 = [
        [  6, 13, 20, 28, 13, 20, 28, 32,
          20, 28, 32, 37, 28, 32, 37, 42 ],
        [ 10, 14, 20, 24, 14, 20, 24, 27,
          20, 24, 27, 30, 24, 27, 30, 34 ]
      ]

      default_scaling8 = [
        [  6, 10, 13, 16, 18, 23, 25, 27,
          10, 11, 16, 18, 23, 25, 27, 29,
          13, 16, 18, 23, 25, 27, 29, 31,
          16, 18, 23, 25, 27, 29, 31, 33,
          18, 23, 25, 27, 29, 31, 33, 36,
          23, 25, 27, 29, 31, 33, 36, 38,
          25, 27, 29, 31, 33, 36, 38, 40,
          27, 29, 31, 33, 36, 38, 40, 42 ],
        [  9, 13, 15, 17, 19, 21, 22, 24,
          13, 13, 17, 19, 21, 22, 24, 25,
          15, 17, 19, 21, 22, 24, 25, 27,
          17, 19, 21, 22, 24, 25, 27, 28,
          19, 21, 22, 24, 25, 27, 28, 30,
          21, 22, 24, 25, 27, 28, 30, 32,
          22, 24, 25, 27, 28, 30, 32, 33,
          24, 25, 27, 28, 30, 32, 33, 35 ]
      ]
      '''

      #print "parse sps begin"
      bitdata = BitReader(data)
      subWidthC = [1, 2, 2, 1]
      subHeightC = [1, 2, 1, 1]
      chroma_format_idc = 1
      crop_left = 0
      crop_right = 0
      crop_top = 0
      crop_bottom = 0
  

      profile_idc = bitdata.read_bits(8)
  
      #print "profile_idc:%s(%d)" % (self.profile_idc_int_to_str(int(profile_idc)), profile_idc)
      constraint_set0_flag = bitdata.read_bits(1)
      constraint_set1_flag = bitdata.read_bits(1)
      constraint_set2_flag = bitdata.read_bits(1)
      
      reserved_zero_5bits = bitdata.read_bits(5)
      print "reserved_zero_5bits:%d" % reserved_zero_5bits

      #constraint_set3_flag = bitdata.read_bits(1)
      #constraint_set4_flag = bitdata.read_bits(1)
      #constraint_set5_flag = bitdata.read_bits(1)
     
      #reserved_zero_5bits = bitdata.read_bits(2)
      level_idc = bitdata.read_bits(8)
      #print "level_idc:%d" % level_idc

      seq_paramter_set_id = bitdata.read_ugolomb()
      if profile_idc == 100 or profile_idc == 110 or profile_idc == 122 or profile_idc == 244 or profile_idc == 44 or profile_idc == 83 or profile_idc == 86 or profile_idc == 118 or profile_idc == 128:
        chroma_format_idc = bitdata.read_ugolomb()
        if chroma_format_idc == 3:
          separate_colour_plane_flag = bitdata.read_bits(1)

        bit_depth_luma_minus8 = bitdata.read_ugolomb()
        bit_depth_chroma_minus8 = bitdata.read_ugolomb()
        qpprime_y_zero_transform_bypass_flag = bitdata.read_bits(1)

        seq_scaling_matrix_present_flag = bitdata.read_bits(1)
        if seq_scaling_matrix_present_flag:
          scaling_matrix4=[[0]*16]*6
          scaling_matrix8=[[0]*64]*2
          default_scaling4=[0]*6
          default_scaling8=[0]*6
          seq_scaling_list_present_flag=[0]*8
          for i in range(chroma_format_idc != 3 and 8 or 12):
            seq_scaling_list_present_flag[i] = bitdata.read_bits(1)
            if seq_scaling_list_present_flag[i]:
              if i < 6:
                self.scaling_list( scaling_matrix4[i], 16, default_scaling4[i])
              else:
                j = i - 6
                self.scaling_list( scaling_matrix8[j], 64, default_scaling8[j] )

      log2_max_frame_num_minus4 = bitdata.read_ugolomb()

      pic_order_cnt_type = bitdata.read_ugolomb()
      if pic_order_cnt_type == 0:
          log2_max_pic_order_cnt_lsb_minus4 = bitdata.read_ugolomb()
      elif (pic_order_cnt_type == 1):
          delta_pic_order_always_zero_flag = bitdata.read_bits(1)
          offset_for_non_ref_pic = bitdata.read_sgolomb()
          offset_for_top_to_bottom_filed = bitdata.read_sgolomb()
          num_ref_frames_in_pic_order_cnt_cycle = bitdata.read_ugolomb()
          offset_for_ref_frame=[]
          for i in range(num_ref_frames_in_pic_order_cnt_cycle):
              offset_for_ref_frame.append(bitdata.read_sgolomb)

      num_ref_frames = bitdata.read_ugolomb()
      gaps_in_frame_num_value_allowed_flag = bitdata.read_bits(1)
      pic_width_in_mbs_minus1 = bitdata.read_ugolomb()
      pic_height_in_map_units_minus1 = bitdata.read_ugolomb()

      frame_mbs_only_flag = bitdata.read_bits(1)
      if not frame_mbs_only_flag:
          mb_adapative_frame_field_flag = bitdata.read_bits(1)
      direct_8x8_inference_flag = bitdata.read_bits(1)

      frame_cropping_flag = bitdata.read_bits(1)
      if frame_cropping_flag:
          frame_crop_left_offset = bitdata.read_ugolomb()
          frame_crop_right_offset = bitdata.read_ugolomb()
          frame_crop_top_offset = bitdata.read_ugolomb()
          frame_crop_bottom_offset = bitdata.read_ugolomb()
         
          crop_left = subWidthC[chroma_format_idc] * frame_crop_left_offset;
          crop_right = subWidthC[chroma_format_idc] * frame_crop_right_offset;
          crop_top = subHeightC[chroma_format_idc] * ( 2 - frame_mbs_only_flag ) *  frame_crop_top_offset;
          crop_bottom = subHeightC[chroma_format_idc] * ( 2 - frame_mbs_only_flag ) * frame_crop_bottom_offset;

      vui_paramaters_present_flag = bitdata.read_bits(1)
      if vui_paramaters_present_flag:
          # vui_paramaters()
          pass

      #print "parse sps end."
      pixel_width = (pic_width_in_mbs_minus1+1)*16 - crop_left - crop_right
      pixel_height = (pic_height_in_map_units_minus1+1)*16 - crop_top - crop_bottom

      return (pixel_width, pixel_height, self.profile_idc_int_to_str(int(profile_idc)),level_idc )

    def packetAssemble(self,rtp):
        red_offset=1
        red_len=1
        F=(ord(rtp.data[red_offset])>>7)&0x1
        NRI=(ord(rtp.data[red_offset])>>5)&0x3
        TYPE=ord(rtp.data[red_offset])&0x1F

        '''
        filename='%sto%s.h264'%(srcipaddr,dstipaddr)
        try:
          if fdout[filename]:
            pass
        except:
           fdout[filename] = open(filename,'w')
        '''
        #print F,NRI, TYPE

        if TYPE==28:#FU-A
          S=(ord(rtp.data[red_offset+1])>>7)&0x1
          E=(ord(rtp.data[red_offset+1])>>6)&0x1
          R=(ord(rtp.data[red_offset+1])>>5)&0x1
          NALTYPE=(ord(rtp.data[red_offset]) & 0xe0) | (ord(rtp.data[red_offset+1] )& 0x1f)
         # print S,E,R,hex(NALTYPE)
          if S == 1:
             if self.firstkeyframe == 1:
                 self.fdout.write(struct.pack('!I',self.nalhead))
                 self.fdout.write(struct.pack('B',int(NALTYPE)))
                 self.fdout.write(rtp.data[red_offset+2:])
                 #print binascii.b2a_hex(rtp.data[:10])
                 #print "start nal pack"
          elif E == 1:
             #print "end nal pack"
             if self.firstkeyframe == 1:
                 self.fdout.write(rtp.data[red_offset+2:])
          else:
            if self.firstkeyframe == 1:
                self.fdout.write(rtp.data[red_offset+2:])

        elif TYPE == 24: #STAP-A
            datalen = len(rtp.data)
            #print 'stap-a len:%d-------------'%datalen

            datalen = datalen - 1

            offset = red_len+1
            while datalen >= 2:

                nalSize = (ord(rtp.data[offset]) << 8) | ord(rtp.data[offset+1]);
                #print 'nalSize len:%d %d '%(nalSize,datalen,)
                if datalen < nalSize + 2 :
                    print 'Discarding malformed STAP-A packet'
                    break;

                if ord(rtp.data[offset+2])&0x1F == 7:
                   self.firstkeyframe = 1

                if self.firstkeyframe == 1:
                    self.fdout.write(struct.pack('!I',self.nalhead))
                    self.fdout.write(rtp.data[offset+2:offset+2+nalSize])
                #print binascii.b2a_hex(rtp.data[offset+2:offset+2+1])

                if ord(rtp.data[offset+2])&0x1F == 7:
                    spsDataIO = StringIO.StringIO(rtp.data[offset+3:])
                    try:
                        ( _w, _h, _profile,_levelid) = self.read_sequence_paramter_set(spsDataIO)
                        if _w != self.width or _h != self.height or _profile != self.profile or _levelid != self.levelid:
                            print "video resolution:%dx%d %s %d" % (_w,_h,_profile,_levelid) 
                            self.width = _w
                            self.height = _h
                            self.profile = _profile
                            self.levelid = _levelid
                    except e:
                        print e

                offset += 2 + nalSize;
                datalen -= 2 + nalSize;

        elif TYPE >= 1 and TYPE <= 23:
            if TYPE == 7 :
              self.firstkeyframe = 1

            if self.firstkeyframe == 1:
              #print hex(ord(rtp.data[0]) )
              self.fdout.write(struct.pack('!I',self.nalhead))
              #print binascii.b2a_hex(rtp.data[0:1])
              self.fdout.write(rtp.data[red_offset:])

            if TYPE==7:
                spsDataIO = StringIO.StringIO(rtp.data[red_offset+1:])
                try:
                    ( _w, _h, _profile,_levelid) = self.read_sequence_paramter_set(spsDataIO)
                    if _w != self.width or _h != self.height or _profile != self.profile or _levelid != self.levelid:
                        print "video resolution:%dx%d %s %d" % (_w,_h,_profile,_levelid) 
                        self.width = _w
                        self.height = _h
                        self.profile = _profile
                        self.levelid = _levelid
                except e:
                    print e


class VP8Assembler(Assembler):
    def __init__(self, outfilename,logger):
        Assembler.__init__(self,outfilename,logger)
        self.skipcnt = 0
        self.firstkeyframe = 0
        self.frameSz=0
        self.seekPos = 32;
        self.packetSz=0;
        self.framecnt = 0;
        self.firstFrame=True
        self.unFinishLen=0;



        headFlg=struct.pack('cccc', 'D', 'K', 'I', 'F')
        self.fdout.write(headFlg)
        version=struct.pack('H', 0x0);
        self.fdout.write(version)
        headSize=struct.pack('H', 32)
        self.fdout.write(headSize)
        fourcc=struct.pack('I', 0x30385056);
        self.fdout.write(fourcc)
        width=struct.pack('BB', 0x80, 0x07);
        self.fdout.write(width)
        height=struct.pack('BB', 0x38, 0x04);
        self.fdout.write(height)
        den=struct.pack('I', 90000);
        self.fdout.write(den)
        num=struct.pack('I', 1);
        self.fdout.write(num)
        framecnt=struct.pack('I', 0xFFFFFFFF);
        self.fdout.write(framecnt)
        unused=struct.pack('I', 0x0);
        self.fdout.write(unused)
        self.framecnt = 0
        self.pixel_width = 0 
        self.pixel_height = 0


    def parse_keyframe_header(self,vpx_data):
        if len(vpx_data) < 10:
            # print "vpx data len less than 10."
            return (0,0)
        if ord(vpx_data[3]) != 0x9d or ord(vpx_data[4]) != 0x01 or ord(vpx_data[5]) != 0x2a:
            # print "vpx data not vpx sync code %x %x %x" % (ord(vpx_data[3]), ord(vpx_data[4]), ord(vpx_data[5]))
            return (0,0)
        pixel_width = ( ord(vpx_data[6])|(ord(vpx_data[7])<<8) )&0x3FFF
        pixel_height = ( ord(vpx_data[8])|(ord(vpx_data[9])<<8) )&0x3FFF
         
        return (pixel_width, pixel_height)

    def parse_payload_header(self, vpx_data):
        key_frame = ord(vpx_data[0])&0x01 and False or True
        if key_frame:
            return self.parse_keyframe_header(vpx_data)
           
        # do not parse other bits.
        # TODO... 
        return (0,0)

    def packetAssemble(self, rtp):       
        #print '%s to %s F:%d NRI:%d type:%d '%(srcipaddr,dstipaddr,F,NRI,TYPE)
        #filename='%sto%s.ivf'%(srcipaddr,dstipaddr)

        red_offset=1
        red_len=1
        offset=red_len;
        X=(ord(rtp.data[red_offset])&0x80)
        S=(ord(rtp.data[red_offset])&0x10)
        PartID=(ord(rtp.data[red_offset])&0xF)
        offset+=1

        if PartID > 8 :
            print 'partid:%d is invalid'%PartID
            return

        if X:
            I=(ord(rtp.data[red_offset+1])&0x80)
            L=(ord(rtp.data[red_offset+1])&0x40)
            T=(ord(rtp.data[red_offset+1])&0x20)
            K=(ord(rtp.data[red_offset+1])&0x10)
            offset+=1
            #print I,L,T,K
            if I:
                pictureId=(ord(rtp.data[red_offset+2])&0x7F)
                offset+=1
                if ord(rtp.data[red_offset+2]) & 0x80 :
                    pictureId=(pictureId<<8)+ord(rtp.data[red_offset+3])
                    offset+=1
                #print 'pictureId %d'%pictureId
            if L:
                offset+=1
            if T or K:
                offset+=1

        #print 'pictureId %d'%pictureId
        if S and self.firstFrame : #begin of partition
            self.firstFrame = False
            self.framecnt+=1;
            (pixel_width, pixel_height) = self.parse_payload_header(rtp.data[offset:])
            if pixel_width > 0 and pixel_height > 0 and (self.pixel_width != pixel_width  or self.pixel_height != pixel_height):
                self.pixel_width = pixel_width  
                self.pixel_height = pixel_height
                print "vp8 resolution:%dx%d" % (pixel_width, pixel_height)
        elif S :
            self.seekPos +=(self.frameSz+12);
            self.frameSz = 0;
            self.unFinishLen = 0;
            self.framecnt+=1;
            (pixel_width, pixel_height) =  self.parse_payload_header(rtp.data[offset:])
            if pixel_width > 0 and pixel_height > 0 and (self.pixel_width != pixel_width  or self.pixel_height != pixel_height):
                self.pixel_width = pixel_width  
                self.pixel_height = pixel_height
                print "vp8 resolution:%dx%d" % (pixel_width, pixel_height)
            #print 'new seek pos %d'%seekPos

        self.packetSz=len(rtp.data) - offset
        self.frameSz += self.packetSz                        
        self.fdout.seek(self.seekPos)
        #print 'seekPos %d'%self.seekPos
        #print 'packetSz %d'%self.packetSz
        self.frameSize = struct.pack('I', self.frameSz);
        self.fdout.write(self.frameSize)
        PTS = struct.pack('Q', rtp.ts);
        self.fdout.write(PTS)
        self.fdout.seek(self.unFinishLen+12+self.seekPos);
        self.unFinishLen +=self.packetSz;

        self.fdout.write(rtp.data[offset:])

        pos=self.fdout.tell();
        #print "rtp.ts  %d"%rtp.ts
        self.fdout.seek(24)
        frameNo = struct.pack('I', self.framecnt);
        self.fdout.write(frameNo);
        self.fdout.seek(pos)
        #print rtp.cc,rtp.m,rtp.p,rtp.pt,rtp.version,rtp.x
        #print hex(rtp.ssrc), rtp.ts, len(rtp.data), binascii.b2a_hex(rtp.data[:2])



    
'''
 dltoff = {
          DLT_NULL:4, DLT_EN10MB:14, DLT_IEEE802:22, DLT_ARCNET:6,
           39            DLT_SLIP:16, DLT_PPP:4, DLT_FDDI:21, DLT_PFLOG:48, DLT_PFSYNC:4,
            40            DLT_LOOP:4, DLT_LINUX_SLL:16 }

         }
'''



def usage():
    print '''
    -h or --help
    -i input file name"
    -o output file name"
    -c codec name h264 or vp8"
    -p payload type"
    '''
    return 

def loginit ():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logoutfile = 'videoAssemble.log'
    fh = TimedRotatingFileHandler(logoutfile,when='M',interval=1,backupCount=30)
    #fh = logging.handlers.RotatingFileHandler(logoutfile,maxBytes=1024*1024,backupCount=40)
     
    # create a file handler
     
    handler = logging.FileHandler(logoutfile)
    handler.setLevel(logging.INFO)
     
    # create a logging format
     
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
     
    # add the handlers to the logger
     
    #logger.addHandler(handler)
    logger.addHandler(fh)
     
    return logger

def main():
    logger = loginit()

    shortargs = 'hi:o:c:p:'
    opts, args = getopt.getopt( sys.argv[1:], shortargs )
    if args:
        print '-h for detail'
        sys.exit(1)

    #initial parameter
    infilename = ''
    outfilename = ''
    codec='h264'
    pt=97

    for opt,val in opts:
        if opt in ( '-h'):
           usage()
           return
        if opt in ( '-i' ):
           infilename = val
           tmp = infilename
           if not cmp('.pcap', tmp[len(tmp)-5:]):
               outfilename = tmp[0:len(tmp)-5]
               outfilename += '.h264'
               print outfilename
           continue
        if opt in ( '-o' ):
           outfilename = val
           continue
        if opt in ( '-c'):
           codec = val
           continue
        if opt in ( '-p' ):
           pt = int(val) &0x7F
           continue
  
    if infilename == '' or outfilename == '' or ((pt >=64 and pt <96) or pt == 255 ) or (codec not in ['h264', 'vp8']):
        print 'infilename=%s outfilename=%s codec=%s pt=%d has invalid parameter!!'%(infilename,outfilename,codec,pt)
        return
    
    inpcap = open(infilename)
    pcap = dpkt.pcap.Reader(inpcap)
    rtpseq =-1
    highseq = 0

    ptlist = []
    if codec == 'h264':
        assember = H264Assembler(outfilename,logger)
    elif codec == 'vp8':
        assember = VP8Assembler(outfilename,logger)


    for ts, buf in pcap:
        #print len(buf)
        if pcap.dloff == 14:
           eth = dpkt.ethernet.Ethernet(buf)
        elif pcap.dloff == 16:
           eth = dpkt.sll.SLL(buf)
        else:
          print pcap.dloff,'is unknown'

        #print eth.data.__class__.__name__
        if eth.data.__class__.__name__=='IP' or eth.data.__class__.__name__ =='str':
            ip = eth.data
            if eth.data.__class__.__name__ =='str':
                print "dpkt str...."
                ip = dpkt.ip.IP(buf)
            #print list(ip.dst),map(ord,list(ip.dst)),tuple(map(ord,list(ip.dst)))
            dstipaddr='%d.%d.%d.%d'%tuple(map(ord,list(ip.dst)))
            srcipaddr='%d.%d.%d.%d'%tuple(map(ord,list(ip.src)))
            testdata=[0x41,0x82]
            
            #print "0x%08x"%nalhead
            #print testdata[1]&0x1F,

            #out.write(struct.pack('!I',nalhead))
            #out.close()
            if ip.data.__class__.__name__=='UDP':
              udp = ip.data

              try:
                rtp = dpkt.rtp.RTP(udp.data)
                
                if rtp.pt not in ptlist:
                    ptlist.append(rtp.pt)
                    print 'payload type list',ptlist

                if rtp.pt == pt :#and '192.168.122.154' == srcipaddr:
                    #print rtp.seq,rtpseq

                    if rtpseq == -1:
                       pass
                    elif (rtpseq +1) != rtp.seq:
                       if rtp.seq < highseq:
                           #print "seq num is wrong."                       
                           pass
                       #print '!!!!!!!!!!  rtp cur seq:%d  pre seq:%d !!!!!!!!!!!!!!'%(rtp.seq, rtpseq)


                    rtpseq = rtp.seq
                    if rtpseq > highseq:
                        highseq = rtpseq
                    #print 'rtpseq %d'%rtpseq

                    try:
                        assember.packetAssemble(rtp)
                    except:
                        continue
              #print rtp.cc,rtp.m,rtp.p,rtp.pt,rtp.version,rtp.x
              #print hex(rtp.ssrc), rtp.ts, len(rtp.data), binascii.b2a_hex(rtp.data[:2])


              except dpkt.dpkt.NeedData:
                 continue
              except dpkt.dpkt.UnpackError:
                 continue   
                
    inpcap.close()              

if __name__=="__main__":
    main()
    
