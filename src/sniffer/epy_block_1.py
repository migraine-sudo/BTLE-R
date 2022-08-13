"""
Whiltening/De-Whitening Blocks:

Inverse whitening of BLE data packets, so that we can parse the PDU format of the link layer then.

Input data: Message data from BLE_Packets_Gain module
"""

import numpy as np
from gnuradio import gr
import pmt
import time

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Whiltening Blocks"""

    def __init__(self, CHANNEL=37):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Whiltening',   # will show up in GRC
            in_sig=None,
            out_sig=None
        )
        self.message_port_register_in(pmt.intern('msg_in'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('msg_out'))
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.channel = CHANNEL
        self.packets_pool=[]

    def handle_msg(self,msg):
        packets=pmt.symbol_to_string(msg)
        #'''
        if packets[:200] in self.packets_pool:
            #print(packets[:200])
            self.packets_pool.append('Empty PDU')
            if len(self.packets_pool) > 3: #5
                self.packets_pool=[]
                #print("clear")
            #print("pass")
            return 0
        #'''     
        self.packets_pool.append(packets[:200])
        index=0
        packets_after = self.whitening(self.channel,packets)
        self.message_port_pub(pmt.intern("msg_out"),pmt.intern(packets_after))
        """
        print("[Before Whitening]:",end='')
        self.logger(packets)
        print("[After   Whitening]:",end='')
        self.logger(packets_after)
        """
        time.sleep(0.01)
        

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

    def logger(self,data):
        index=0
        print("[",end='')
        for i in range(int(len(data)/8)):
                    Bytes=[data[x] for x in range(index,index+4)]
                    Bytes2=[data[x] for x in range(index+4,index+8)]
                    print(format(int("".join(Bytes2[::-1]),2),'x')+format(int("".join(Bytes[::-1]),2),'x'),end='') # Bits need reverse
                    #print("0x"+format(int("".join(Bytes),2),'x')+format(int("".join(Bytes2),2),'x'),end=' ') 
                    index+=8
        print("]")

    def reset_channel(self,channel):
        self.channel = channel