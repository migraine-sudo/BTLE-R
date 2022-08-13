"""
BLE_PDU_Decode Blocks:
"""

from distutils.debug import DEBUG
from email.headerregistry import Address
import numpy as np
from gnuradio import gr
import pmt
import time
import binascii

Debug = False


class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Whiltening Blocks"""

    def __init__(self, CHANNEL = 37,CRCINIT = '0x555555',ADVADDRESS = ''):  # only default arguments here
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
        self.crcinit = CRCINIT
        self.advA = ADVADDRESS

    def handle_msg(self,msg):
        self.output={'Channel':self.channel,'pdu_payload':{}}

        packets=pmt.symbol_to_string(msg)
        packet_str = self.bit2str(packets) # Convert the bitstream to a string, modify the bits order
        
        len = self.PDU_Len(packet_str)
        packet_str = packet_str[:len*2+20] # minus the excess at the end

        # Start Parse PDU
        self.AA_Gain(packet_str)
        self.PDU_Payload(packet_str)
        self.PDU_CRC(packet_str)

        try:
            CRCInit=int(self.crcinit,base=16)
        except:
            print("[Warning] the type of CRCInit should be string,using 0x555555 Default")
            CRCInit=0x555555
        '''
        crc_ca=self.PDU_CRC_CAL(self.output['head']+self.output['payload'],crcinit=CRCInit) #crc_ca=self.PDU_CRC_CAL(packet_str[10:len*2+14])
        if crc_ca !=int(self.output['crc'],base=16): # CRC Check
            if DEBUG:
                print("[LOG] Drop packets [CRC wrong]\n")
            return 0
        '''

        '''
        Parse
        '''

        if self.channel in [37,38,39]:
            """Advertising Physical Channel PDU"""
            try:
                self.ADV_HEAD_Parse(packet_str) ## Parse Header
            except:
                print("PDU Header Parsing Error")
                return False
            try:
                if self.PDU_Type[self.output['type']] != 'CONNECT_IND':
                    crc_ca=self.PDU_CRC_CAL(self.output['head']+self.output['payload'],crcinit=CRCInit) #crc_ca=self.PDU_CRC_CAL(packet_str[10:len*2+14])
                    if crc_ca !=int(self.output['crc'],base=16): # CRC Check
                            if Debug:
                                print("[LOG] Drop packets [CRC wrong]\n")
                            return False

                else:
                    crc_ca=self.PDU_CRC_CAL(self.output['head']+self.output['payload'],crcinit=CRCInit) #crc_ca=self.PDU_CRC_CAL(packet_str[10:len*2+14])
                    if crc_ca !=int(self.output['crc'],base=16): # CRC Check
                            if Debug:
                                print("[LOG] CONNECT_IND packets [CRC wrong]")
                            self.output['crc'] += '[Wrong]'
                            #return 0
            except:
                return False
            self.ADV_Payload_Parse(self.output['type'],self.output['payload']) ## Parse Payload
            try:
                if self.output['pdu_payload']['AdvA']!="": 
                    if self.advA.upper() !='' and self.advA.upper() != self.output['pdu_payload']['AdvA'].upper():
                        #print("DROP")
                        return False
            except:
                if self.advA.upper() !='':
                    return False
        else:
            """Data Physical Channel PDU"""
            print("Data Physical Channel PDU")

        """LOG"""
        if Debug == True:
        #if self.PDU_Type[self.output['type']]=='CONNECT_IND':
            print ("PACKETS —> ["+packet_str+"]")
            print ('    [CH]:'+str(self.channel),end=' ')
            print ('    [AA]:0x'+self.output['AA'].upper(),end='')
            if self.channel in [37,38,39]:
                """Advertising Physical Channel PDU"""      
                try:
                    print ("    [Type]  : "+self.PDU_Type[self.output['type']],end=' ')
                    print ("    [ChSel] : "+self.PDU_CHSEL[self.output['ChSel']],end=' ')
                    print ("    [TxAdd] : "+self.PDU_Add[self.output['TxAdd']],end=' ')
                    print ("    [RxAdd] : "+self.PDU_Add[self.output['RxAdd']])
                    print ("     |----- [PDU] : " + str(self.output['pdu_payload']))
                except:
                    if Debug:
                        print("Invaild PDU Header")
                    return 0
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
            '0011':'SCAN_REQ',  #AUX_SCAN_REQ
            '0100':'SCAN_RES',
            '0101':'CONNECT_IND',   #AUX_CONNECT_REQ
            '0110':'ADV_SCAN_IND',
            '0111':'ADV_EXT_IND',   #AUX_ADV_IND/AUX_SCAN_RSP/AUX_SYNC_IND/AUX_CHAIN_IND
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
    PDU Type && RFU && ChSel && TxAdd && RxAdd
    '''
    def ADV_HEAD_Parse(self,data):
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

    '''
    ADV Payload Decode
    Supported PDU Type
        'ADV_IND','ADV_DIRECT_IND','ADV_NONCONN_IND','ADV_SCAN_IND','SCAN_RSP','SCAN_REQ','CONNECT_IND'
    Unsupported PDU Type
        'AUX_*'
    '''
    
    def ADV_Payload_Parse(self,type,payload):
        try:
            if self.PDU_Type[type] in ['ADV_IND','ADV_DIRECT_IND','ADV_NONCONN_IND','ADV_SCAN_IND','SCAN_RSP']:
                AdvAddress = ""
                for i in range(6):
                    AdvAddress += payload[10-i*2]+payload[11-i*2]+":"
                self.output['pdu_payload']['AdvA']=AdvAddress[:-1]
                #self.output['pdu_payload']['AdvA_test']=self.lsb2msb(payload,0,6)

                if self.PDU_Type[type] in ['ADV_IND','ADV_NONCONN_IND','ADV_SCAN_IND']:
                    self.output['pdu_payload']['AdvData']=payload[12:]
                elif self.PDU_Type[type] == 'SCAN_RSP':
                    self.output['pdu_payload']['ScanRspData']=payload[12:]
                elif self.PDU_Type[type] == 'ADV_DIRECT_IND':
                    TargetA = ""
                    for i in range(6):
                        TargetA += payload[22-i*2]+payload[23-i*2]+":"
                    self.output['pdu_payload']['TargetA']=TargetA[:-1]

            if self.PDU_Type[type] in ['SCAN_REQ']:
                ScanA = ""
                AdvA = ""
                for i in range(6):
                    ScanA += payload[10-i*2]+payload[11-i*2]+":"
                self.output['pdu_payload']['ScanA']=ScanA[:-1]
                for i in range(6):
                    AdvA += payload[22-i*2]+payload[23-i*2]+":"
                    self.output['pdu_payload']['AdvA']=AdvA[:-1]

            # Most Important Part
            if self.PDU_Type[type] in ['CONNECT_IND']:
                InitA = AdvA = ""
                for i in range(6):
                    InitA += payload[10-i*2]+payload[11-i*2]+":"
                self.output['pdu_payload']['InitA']=InitA[:-1]
                for i in range(6):
                    AdvA += payload[22-i*2]+payload[23-i*2]+":"
                    self.output['pdu_payload']['AdvA'] = AdvA[:-1]
                # LL_Data Parse    
                AA = CRCinit = WinSize = Interval = Latency = Timeout = ChM = Hop = SCA = ""
                LL_Data=payload[24:]
                self.output['pdu_payload']['LLData'] = LL_Data
                self.output['pdu_payload']['LLData_parse'] = {}

                self.output['pdu_payload']['LLData_parse']['AA']=self.lsb2msb(LL_Data,0,4)
                self.output['pdu_payload']['LLData_parse']['CRCInit']=self.lsb2msb(LL_Data,4,3)
                self.output['pdu_payload']['LLData_parse']['WinSize']=self.lsb2msb(LL_Data,7,1)
                self.output['pdu_payload']['LLData_parse']['WinOffset']=self.lsb2msb(LL_Data,8,2)
                self.output['pdu_payload']['LLData_parse']['Interval']=self.lsb2msb(LL_Data,10,2)
                self.output['pdu_payload']['LLData_parse']['Latency']=self.lsb2msb(LL_Data,12,2)
                self.output['pdu_payload']['LLData_parse']['Timeout']=self.lsb2msb(LL_Data,14,2)
                self.output['pdu_payload']['LLData_parse']['ChM']=self.lsb2msb(LL_Data,16,5)
                HopSCA=self.lsb2msb(LL_Data,21,1)
                self.output['pdu_payload']['LLData_parse']['Hop']=str(int(bin(int(HopSCA,base=16))[2:][-5:],2))
                self.output['pdu_payload']['LLData_parse']['SCA']=str(int(bin(int(HopSCA,base=16))[2:][:3],2))
        except:
            pass
            #print("[Error] Invaild PDU Type or PDU is Broken")

    def lsb2msb(self,payload,start,length):
        msb=""
        for i in range(length):
            msb += payload[start*2+length*2-2-i*2]+payload[start*2+length*2-1-i*2]
        return msb


    def reset_channel(self,channel):
        self.channel = channel
    
    def reset_crcinit(self,crcinit):
        self.crcinit = crcinit
    
    def reset_addr(self,addr):
        self.advA = addr