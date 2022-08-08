"""
BLE_Packets_Gain Block

The input data comes from GFSKDemod, which captures BLE air packets according to PREAMBLE and AccessAddress. 
According to the longest value of BLE Packets, forward the data to the next module for processing. 

Key1: Not descrambled, not calculated PDU length
Key2: Since the output length of GFSKDemod is 1024 each time, some packets may be truncated,
      and the module will choose to discard these packets.

Param1: Access Address , ADV (0x8E89BED6) Default

"""

from re import L
from struct import pack
import numpy as np
from gnuradio import gr
from array import array
import pmt


class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """ BLE_Packets_Gain Block """

    def __init__(self, AA = "0x8E89BED6"):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='BLE PACKET Gain',   # will show up in GRC
            in_sig=[np.int8],
            out_sig=None
        )
        self.message_port_register_out(pmt.intern('msg_out'))

        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.AccessAddress = AA
        self.last_packets=""
        self.packets_buf = ""

    def work(self, input_items, output_items):
        bits_stream=input_items[0]
        bits_decode=""
        Octets = 257 #47

        for x in bits_stream:  
            bits_decode+=str(x)

        # Fix packets cut
        if len(self.packets_buf)!=0:
            #print("fix packets")
            self.packets_buf += bits_decode[:Octets-len(self.packets_buf)]
            self.message_port_pub(pmt.intern("msg_out"),pmt.intern(self.packets_buf))
            self.packets_buf = ""
            return len(input_items[0])

        if self.AccessAddress!='':
            AA =bin(int(self.AccessAddress,base=16))[2:].zfill(8*4)[::-1]
        else:
            AA=""
        PREAMBLE="01010101" # 0xaa reverse
        PREAMBLE2="10101010" # 0x55 reverse
        #AA = "01101011011111011001000101110001" #Access Address = 0x8E89BED6
        
        packet1 = PREAMBLE+AA
        packet2 = PREAMBLE2+AA

        if packet1 in bits_decode or packet2 in bits_decode :
            if packet1 in bits_decode:
                index = bits_decode.find(packet1)
            else:
                index = bits_decode.find(packet2)
            
            if len(bits_decode) - index >= Octets*8:    # Cut pakcets
                packets = bits_decode[index:index+Octets*8]
            else:
                self.packets_buf = bits_decode[index:] # Fix packets
                return len(input_items[0])   
            
            '''
            if packets[(Octets-3)*8:] == self.last_packets:  # Deduplication according to CRCs
                return len(input_items[0]) 
            else:
                self.last_packets=packets[(Octets-3)*8:]
            '''
            if True:
                # Debug Log
                '''
                print("\n[",end='')
                index=0
                for i in range(0,47):
                    Bytes=[packets[x] for x in range(index,index+4)]
                    Bytes2=[packets[x] for x in range(index+4,index+8)]
                    print("0x"+format(int("".join(Bytes2[::-1]),2),'x')+format(int("".join(Bytes[::-1]),2),'x'),end=' ') # Bits need reverse
                    index+=8                
                print("]")
                '''
                self.message_port_pub(pmt.intern("msg_out"),pmt.intern(packets))
                return len(input_items[0])
        '''
        
        if packet2 in bits_decode:
            index = bits_decode.find(packet2)
            print("[",end='')
            for i in range(0,47):
                try:
                    Bytes=[bits_decode[x] for x in range(index,index+4)]
                    Bytes2=[bits_decode[x] for x in range(index+4,index+8)]
                    print("0x"+format(int("".join(Bytes2[::-1]),2),'x')+format(int("".join(Bytes[::-1]),2),'x'),end=' ') # Bits need reverse
                except:
                    print("decode fail")
                    break    
                index+=8
            print("]")
        
        '''
        return len(input_items[0])
        #return len(output_items[0])
        #output_items[0][:] = input_items[0] * self.example_param

    def reset_accaddr(self,aa):
        self.AccessAddress = aa