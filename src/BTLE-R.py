#!/opt/local/bin/python

import sys
sys.path.append('./sniffer/')

from bisect import bisect_left
from pickle import TRUE

import ble_decode
import signal
import sys
import time
import zmq
import threading
import getopt
import subprocess

usage = """
usage: BTLE-R.py [-h] [-v] [-m MAC] [-c CH] [-t FILE]

Command Line Interface for BTLE-Radio Bluetooth Baseband Experiment Kit

optional arguments:
  -h, --help                Show this help message and exit
  -v, --version             Show version and exit
  -m MAC, --mac MAC         Filter packets by advertiser MAC
  -c CH, --channel CH       Monitor the broadcast channel CHA, the range is 0-39, the default is 37-39
  -t FILE, --transfer FILE  Send link layer data, data from JSON file [ Example in src/transfer/packets.txt ]
"""


"""
The RADIO module controller controls the BLE baseband written by GNURadio. 
Support frequency hopping, BLE air interface unpacking, etc.
"""
T_IFS = 150

class RADIO:
    def __init__(self,tb) -> None:
        self.tb = tb    #GNURadio top_block_cls
        self.sniff_adv_on = False
        self.channel_list = [37,38,39]
        # Start Threads
        self.thread_sniff = threading.Thread(target=self.hop_on_adv_cha)
        self.thread_sniff.setDaemon(True)
        self.thread_sniff.start()
        
    def filter(self,addr='',channel = -1):
        if addr!='':
            self.tb.epy_block_2.reset_addr(addr)
        if channel != -1:
            self.channel_list = []
            self.channel_list.append(int(channel))

    def start_sniff(self):
        self.sniff_adv_on = True  
        print("[*] Start Sniff")

    def stop_sniff(self):
        self.sniff_adv_on = False

    # In-thread loop frequency hopping, controlled 
    # by calling start_sniff or stop_sniff
    def hop_on_adv_cha(self):
        while True:
            while self.sniff_adv_on:
                for c in self.channel_list:
                    self.HopChannel(c)
                    time.sleep(1.05) 
                    #time.sleep(T_IFS*0.000001)

    # The channel number corresponds to the actual frequency
    def HopChannel(self,channel,crcint='0x555555'):
        freq = self.channel_map[channel]
        self.tb.set_freq_channel(freq)
        self.tb.epy_block_1.reset_channel(channel)
        self.tb.epy_block_2.reset_channel(channel)
        self.tb.epy_block_2.reset_crcinit(crcint)
    
    # CHANNLE MAP DICT
    channel_map = {37:2.402e9,38:2.426e9,39:2.480e9,
        0:2.404e9,1:2.406e9,2:2.408e9,3:2.410e9,4:2.412e9,5:2.414e9,6:2.416e9,7:2.418e9,8:2.420e9,9:2.422e9,10:2.424e9,
        11:2.428e9,12:2.430e9,13:2.432e9,14:2.434e9,15:2.436e9,16:2.438e9,17:2.440e9,18:2.442e9,19:2.444e9,20:2.446e9,
        21:2.448e9,22:2.450e9,23:2.452e9,24:2.454e9,25:2.456e9,26:2.458e9,27:2.460e9,28:2.462e9,29:2.464e9,30:2.466e9,
        31:2.468e9,32:2.470e9,33:2.472e9,34:2.474e9,35:2.476e9,36:2.478e9}  # Using tools/chm_gen.py

class BLE_Decode:
    def __init__(self) -> None:
        pass

    def show(self,message):
        """LOG"""
        LOG = True
        self.output=eval(message[3:].decode('utf-8'))
        if LOG == True:
        #if self.PDU_Type[self.output['type']]=='CONNECT_IND':
            #print ("PACKETS —> ["+packet_str+"]")
            print ('    [CH]:'+str(self.output['Channel']),end=' ')
            print ('    [AA]:0x'+self.output['AA'].upper(),end='')
            if self.output['Channel'] in [37,38,39]:
                """Advertising Physical Channel PDU"""      
                try:
                    print ("    [Type]  : "+self.PDU_Type[self.output['type']],end=' ')
                    print ("    [ChSel] : "+self.PDU_CHSEL[self.output['ChSel']],end=' ')
                    print ("    [TxAdd] : "+self.PDU_Add[self.output['TxAdd']],end=' ')
                    print ("    [RxAdd] : "+self.PDU_Add[self.output['RxAdd']])
                    print ("     |----- [PDU] : " + str(self.output['pdu_payload']))
                except:
                    #print("Invaild PDU Header")
                    pass
            else:
                """Data Physical Channel PDU"""
                print("Data Physical Channel PDU")
            
            print ("    [PAYLOAD] : ["+self.output['payload']+"]",end='')
            #print ("    [LEN : "+str(len),end='')
            print ("    , CRC : "+self.output['crc']+"]\n")

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

def main(top_block_cls=ble_decode.ble_decode, options=None):

    try:
        opts,args = getopt.getopt(sys.argv[1:],'-h-m:-v-c:-t:',['help','mac=','version','channel=','transfer='])
    except:
        print(usage)
        exit()
    macaddr=''
    channel=-1
    for opt_name,opt_value in opts:

            if opt_name in ('-h','--help'):
                print(usage)
                exit()
            if opt_name in ('-v','--version'):
                print("[*] Version is 0.01 ")
                exit()
            if opt_name in ('-m','--mac'):
                macaddr = opt_value
                #exit()
            if opt_name in ('-c','--channel'):
                channel = opt_value
            if opt_name in ('-t','--transfer'):
                subprocess.run(["transfer/trans_interface.py",opt_value])
                exit()
    
    tb = top_block_cls()
    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    def init_zmq(addr):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(addr)
        socket.setsockopt_string(zmq.SUBSCRIBE,"")
        return socket

    socket = init_zmq("tcp://127.0.0.1:52855") # Init ZMQ

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    tb.start() 

    # Radio Control
    radio = RADIO(tb)
    radio.filter(addr=macaddr,channel=channel)
    radio.start_sniff()

    ble = BLE_Decode()
    while True:
        output= socket.recv()
        ble.show(output)
    #tb.wait()
    

if __name__ == '__main__':
    main()