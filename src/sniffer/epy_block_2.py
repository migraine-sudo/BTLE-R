"""
BLE_PDU_Decode Blocks:

"""

import numpy as np
from gnuradio import gr
import pmt
import time
import binascii

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Whiltening Blocks"""

    def __init__(self, CHANNEL = 37):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='BLE PDU Decode',   # will show up in GRC
            in_sig=None,
            out_sig=None
        )
        self.message_port_register_in(pmt.intern('msg_in'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('msg_out'))
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.channel = CHANNEL
        self.output={'Channel':self.channel}

    def handle_msg(self,msg):
        packets=pmt.symbol_to_string(msg)
        packet_str = self.bit2str(packets) # Convert the bitstream to a string, modify the bits order
        
        len = self.PDU_Len(packet_str)
        packet_str = packet_str[:len*2+20] # minus the excess at the end

        # Start Parse PDU
        self.AA_Gain(packet_str)
        self.PDU_Payload(packet_str)
        self.PDU_CRC(packet_str)

        crc_ca=self.PDU_CRC_CAL(self.output['head']+self.output['payload']) #crc_ca=self.PDU_CRC_CAL(packet_str[10:len*2+14])
        if crc_ca !=int(self.output['crc'],base=16):
            print("[LOG] Drop packets [CRC wrong]\n")
            return 0
        '''
        LOG
        '''
        print ("PACKETS —> ["+packet_str+"]")
        print ('    [CH]:'+str(self.channel),end=' ')

        if self.channel in [37,38,39]:
            """Advertising Physical Channel PDU"""
            self.PDU_ADV_Parse(packet_str) ## Parse Header
            '''Log'''
            try:
                print ("    [Type]  : "+self.PDU_Type[self.output['type']],end=' ')
                print ("    [ChSel] : "+self.PDU_CHSEL[self.output['ChSel']],end=' ')
                print ("    [TxAdd] : "+self.PDU_Add[self.output['TxAdd']],end=' ')
                print ("    [RxAdd] : "+self.PDU_Add[self.output['RxAdd']])
            except:
                print("Invaild PDU Header")
        else:
            """Data Physical Channel PDU"""
            print("Data Physical Channel PDU")
        
        print ("    [PAYLOAD] : ["+self.output['payload']+"]",end='')
        print ("    [LEN : "+str(len),end='')
        print ("    , CRC : "+self.output['crc']+"]\n")

        
        self.message_port_pub(pmt.intern("msg_out"),pmt.intern(str(self.output)))

    '''
    PDU Help Dict
    '''
    PDU_Type={
            '0000':'ADV_IND',
            '0001':'ADV_DIRECT_IND',
            '0010':'ADV_NONCONN_IND',
            '0011':'SCAN_REQ',
            '0100':'SCAN_RES',
            '0101':'CONNECT_IND',
            '0110':'ADV_SCAN_IND',
            '0111':'ADV_EXT_IND',
            '1000':'AUX_CONNECT_RSP'
        }
    PDU_Add={
            '0':'Public',
            '1':'Random'
        }
    PDU_CHSEL={
            '0':'#1',
            '1':'#2'
        }
        
    '''
    Bits to String
    Reverse the byte order of the bit stream and convert it to string format
    The endianness is the same as wireshark shows.
    '''
    def bit2str(self,data):
        str=""
        index=0
        for i in range(int(len(data)/8)):
            Bytes=[data[x] for x in range(index,index+4)]
            Bytes2=[data[x] for x in range(index+4,index+8)]
            str+=format(int("".join(Bytes2[::-1]),2),'x')+format(int("".join(Bytes[::-1]),2),'x') # Bits need reverse
            index+=8
        return str

    """
    Access Address Gain
    """
    def AA_Gain(self,data):
        data_lsb = data[2:10]
        aa = self.lsb2value(data_lsb)
        #for i in range(4): 
        #    aa += data_lsb[(3-i)*2]+data_lsb[(3-i)*2+1]
        self.output['AA']=aa
        #return aa

    '''
    PDU payload len Gain
    '''
    def PDU_Len(self,data):
        #data_lsb = data[10:12]
        data_lsb = data[12:14]
        pdu_len = self.lsb2value(data_lsb)
        return int(pdu_len,base=16)

    '''
    PDU Type && RFU && ChSel && TxAdd && RxAdd
    '''
    def PDU_ADV_Parse(self,data):
        data_lsb = data[10:12]
        pdu_type = bin(int(data_lsb[1],base=16))[2:].zfill(4)
        bits = bin(int(data_lsb[0],base=16))[2:].zfill(4)[::-1]  #fix endianness
        pdu_rfu = bits[0]
        pdu_ChSel = bits[1]
        pdu_TxAdd = bits[2]
        pdu_RxAdd = bits[3]
        ## Return
        self.output['type']=pdu_type 
        self.output['rfu']=pdu_rfu
        self.output['ChSel']=pdu_ChSel
        self.output['TxAdd']=pdu_TxAdd
        self.output['RxAdd']=pdu_RxAdd

        
    def PDU_Payload(self,data):
        self.output['head']=data[10:14] # PDU header
        self.output['payload']=data[14:-6]  # PDU payload

    '''
    PDU CRC Gain
    '''
    def PDU_CRC(self,data):
        crc = data[-6:]
        crc_re=""
        #for i in range(len(crc)):       
            #crc_re+=hex(int(bin(int(crc[i],base=16))[2:].zfill(4)[::-1],2))[2:]
        #print(crc)
        for i in range(3):
            crc_re+=crc[(2-i)*2]+crc[(2-i)*2+1]
        self.output['crc'] ="0x" + crc_re

    def PDU_CRC_CAL(self,data,crcinit=0x555555):
        data_re=""
        #Restoring the byte order to the original order during Bluetooth transmission 
        #is actually a bit redundant and worth optimizing.
        for i in range(int(len(data)/2)):
            data_re +=hex(int((bin(int(data[i*2],base=16))[2:].zfill(4) + bin(int(data[i*2+1],base=16))[2:].zfill(4))[::-1],base=2) )[2:].zfill(2)
        payload = binascii.unhexlify(data_re)
        crc24 = self.crc24(payload,crcinit)
        return int(bin(crc24)[2:].zfill(24)[::-1],2) # reverse bits

    def crc24(self,octets,crcint):
        INIT = crcint
        POLY = 0x100065B
        crc = INIT
        for octet in octets: # this is what the '*octets++' logic is effectively
        # accomplishing in the C code.
            crc ^= (octet << 16)
            # Throw that ROL function away, because the C code **doesn't** actually
            # rotate left; it shifts left. It happens to throw away any bits that are
            # shifted past the 32nd position, but that doesn't actulaly matter for
            # the correctness of the algorithm, because those bits can never "come back"
            # and we will mask off everything but the bottom 24 at the end anyway.
            for i in range(8):
                crc <<= 1
                if crc & 0x1000000: crc ^= POLY
        return crc & 0xFFFFFF


    '''
    Parse the little-endian data byte sequence to get the real value of this field
    (provided that the metadata comes from bit2str)
    '''
    def lsb2value(self,data):
        length = int(len(data)/2)
        str=""
        for i in range(length): 
            str += data[(length-1-i)*2]+data[(length-1-i)*2+1]
        return str