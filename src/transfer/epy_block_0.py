"""
BLE Radio Module:

The BLE air interface is sent, the data is automatically packaged and the CRC is calculated,
and the output can directly transmit the data stream from the physical layer.
"""

from email.charset import add_alias
import re
from time import time
import time
from zipapp import create_archive
import numpy as np
from gnuradio import gr
import array
import binascii

T_IFS = 150
DEBUG = True

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """BLE Radio Module - link layer to physical layer conversion"""

    def __init__(self, channel=38 ,crcinit="0x555555" ,accaddr="0x8E89BED6" ,pdu_data ="022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779"):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='BLE_Radio_Source',   # will show up in GRC
            in_sig=[],
            out_sig=[np.int8]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.channel = channel
        self.pdu_data = pdu_data
        self.crcinit = int(crcinit,16)
        self.accaddr = int(accaddr,16)
        self.rf_buffer = ""
        self.empty_flag = False
        self.num = 0

    def work(self, input_items, output_items):

        PDU_Data = self.pdu_data #"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779" #37-DISCOVERY-TxAdd-0-RxAdd-0-AdvA-010203040506-LOCAL_NAME09-SDR/Bluetooth/Low/Energy
        self.rf_buffer  = self.LL_Data_Pack(PDU_Data,accaddr=self.accaddr,crcinit = self.crcinit)

        packets = self.RF_Trans()
        try:
            for j in range(len(packets)):
                output_items[0][j] = packets[j]
        except:
            output_items[0]=np.array([0 for i in range(len(packets))]) 
            output_items[0][:len(packets)] = packets
        return len(output_items[0][:len(packets)])


    '''
    The data modulation is modulated and transmitted to the HackRF transmitter
    '''
    def RF_Trans(self):
        source_bits = self.str2bits(self.rf_buffer)
        packets = array.array('B',source_bits.encode())
        self.rf_buffer = ""
        if self.empty_flag == False:
            self.num += 1
        if DEBUG and self.empty_flag == False:
            print(f"send {str(self.num)} packets")
        time.sleep(T_IFS*0.000001)
        #time.sleep(T_IFS*0.001)
        return packets

    '''
    Link layer data packets only need to provide PDU data, 
    but please ensure that the PDU Header and PDU Data are self-consistent, 
    and will not be checked here.
    '''
    def LL_Data_Pack(self,payload,accaddr = 0x8E89BED6,crcinit = 0x555555):
        if len(payload) == 0 or len(payload)%2 ==1:
            if DEBUG:
                if len(payload) == 0:
                    print("Empty PDU")
                else:
                    print("[Error] The hexadecimal parsing of the PDU failed, please ensure that the number of bytes is a multiple of 2")
            return ""
        if payload == "E7":
            self.empty_flag = True
        LL_Data = self.add_crc_sum(self.add_accadddr(payload,accaddr),crcinit)
        PHY_Data = self.data_whitening(self.channel,LL_Data)
        if DEBUG and payload != "E7": # "E7" -> EMPTY FLAG
            print ("CH : " + str(self.channel))
            print ("LL Data Before Whitening : " + LL_Data)
            print ("PHY Data After Whitening : " + PHY_Data)
        return PHY_Data


    '''
    Use 0xaa or 0x55 as Preamble according to the lowest bit of AccessAddress
    '''
    # Attention : Using After add_accadddr() !
    def add_preamble(self,payload,low_bit = 0):
        #PREAMBLE="01010101" # 0xaa reverse
        #PREAMBLE2="10101010" # 0x55 reverse
        if low_bit == 0 :
            PREAMBLE_HEX = "aa"
        elif low_bit == 1:
            PREAMBLE_HEX = "55"
        else:
            return False
        return PREAMBLE_HEX + payload 

    '''
    Add AccessAddress and Preamble to the header for the PDU packet
    '''
    def add_accadddr(self,payload,accaddr = 0x8E89BED6):
        #Broadcast = "01101011011111011001000101110001" # 0x8E89BED6
        accaddr_list = list(hex(accaddr)[2:])
        accaddr_hex = ""
        for i in range(0,int(len(accaddr_list)/2)):
            accaddr_hex+=accaddr_list[int(len(accaddr_list))-i*2-2]+accaddr_list[int(len(accaddr_list))-i*2-1]
        payload = accaddr_hex+payload
        if int(bin(int(hex(accaddr)[-2:],16))[-1:]) == 0:
            return self.add_preamble(payload,0)    
        return self.add_preamble(payload,1)


    '''
    Calculate the CRC of the entire PDU and add it to the end of the PDU
    '''
    def add_crc_sum(self,payload,crcinit=0x555555):
        ''' Usage:
            source  = "aad6be898e0011727919bebae70201050702031802180418" #d1a136
            source = self.add_crc_sum(source)
            print(source)
        '''
        crc24 = self.PDU_CRC_CAL(payload[10:],crcinit=crcinit,reverse=False) # Cut Preamble && AccAddr
        if crc24 == 0: #The CRC check is 0, indicating that the PDU we obtained contains CRC at the end.
            return payload
        payload += self.bit2str(bin(crc24)[2:]).zfill(6) # crc bug fix
        return payload

    '''
    For whitening the entire PDU, Channle is required as ca. 
    Note that Preamble and AccessAddress are added before whitening.
    '''
    def data_whitening(self,channel,payload):
        source_bits = self.str2bits2(payload)
        ret = self.bit2str(self.whitening(channel,source_bits))
        return ret



    '''
    BLE Tools Blow...
    -----------------
    '''
    def PDU_CRC_CAL(self,data,crcinit=0x555555,reverse =True):
        data_re=""
        #Restoring the byte order to the original order during Bluetooth transmission 
        #is actually a bit redundant and worth optimizing.
        for i in range(int(len(data)/2)):
            data_re +=hex(int((bin(int(data[i*2],base=16))[2:].zfill(4) + bin(int(data[i*2+1],base=16))[2:].zfill(4))[::-1],base=2) )[2:].zfill(2)
        payload = binascii.unhexlify(data_re)
        crc24 = self.crc24(payload,crcinit) 
        if reverse == True:
            return int(bin(crc24)[2:].zfill(24)[::-1],2) # reverse bits
        return crc24

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

    def whitening(self,channel,data):
        pre = data[:40]
        data= data[40:]
        position=[]
        register=bin(channel)[2:].zfill(6)
        #print(register)
        position.append(1)
        for i in register:
            position.append(int(i))
        #print("init position:"+"".join([str(x) for x in position]))

        sink=[]
        for x in data:
            extra = position[6]
            sink.append(extra^int(x))
            position[6]=position[5]
            position[5]=position[4]
            position[4]=position[3]^extra
            position[3]=position[2]
            position[2]=position[1]
            position[1]=position[0]
            position[0]=extra
        return pre+"".join([str(x) for x in sink])


    '''
    str2bits
    '''
    def str2bits(self,source):
        bit_stream=""
        for index in range(int(len(source)/2)):
            #print(i)
            bits1=(bin(int(source[index*2],base=16)))[2:].zfill(4)
            bits2=(bin(int(source[index*2+1],base=16)))[2:].zfill(4)
            bits_list = list(bits1+bits2)
            for i in range(len(bits_list)):
                bits_list[i] = chr(int(bits_list[i]))
                #bits_list[i] = (bits_list[i])
            #print((bits1+bits2)[::-1])
            bit_stream+=("".join(bits_list))[::-1]
            #bit_stream+=(bits2+bits1)
        return bit_stream

    '''
    str2bits2,little different from str2bits
    '''
    def str2bits2(self,source):
        bit_stream=""
        for index in range(int(len(source)/2)):
            #print(i)
            bits1=(bin(int(source[index*2],base=16)))[2:].zfill(4)
            bits2=(bin(int(source[index*2+1],base=16)))[2:].zfill(4)
            bits_list = list(bits1+bits2)
            for i in range(len(bits_list)):
                #bits_list[i] = chr(int(bits_list[i]))
                bits_list[i] = (bits_list[i])
            #print((bits1+bits2)[::-1])
            bit_stream+=("".join(bits_list))[::-1]
            #bit_stream+=(bits2+bits1)
        return bit_stream

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
    Interface to reset
    '''

    def reset_pdu_data(self,payload):
        self.pdu_data = payload
    
    def reset_crcinit(self,crcinit):
        self.crcinit = crcinit

    def reset_accaddr(self,accaddr):
        self.accaddr = accaddr

    def reset_channel(self,channel):
        self.channel = channel