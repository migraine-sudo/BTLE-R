#!/opt/local/bin/python

from asyncore import read
from struct import pack
from xmlrpc.client import FastParser
from ble_send import ble_send
from queue import Queue
import sys
import os
import signal
import time
import json
import socket
import threading

T_IFS = 150
MODEL = 1

channel_map = {37:2.402e9,38:2.426e9,39:2.480e9,
        0:2.404e9,1:2.406e9,2:2.408e9,3:2.410e9,4:2.412e9,5:2.414e9,6:2.416e9,7:2.418e9,8:2.420e9,9:2.422e9,10:2.424e9,
        11:2.428e9,12:2.430e9,13:2.432e9,14:2.434e9,15:2.436e9,16:2.438e9,17:2.440e9,18:2.442e9,19:2.444e9,20:2.446e9,
        21:2.448e9,22:2.450e9,23:2.452e9,24:2.454e9,25:2.456e9,26:2.458e9,27:2.460e9,28:2.462e9,29:2.464e9,30:2.466e9,
        31:2.468e9,32:2.470e9,33:2.472e9,34:2.474e9,35:2.476e9,36:2.478e9}  # Using tools/chm_gen.py

usage = '''The structure of the Packet file is wrong, the sample reference is as follows：
packets.txt
-----------
# ADV_IND CHANNLE 37 TxAdd 1 RxAdd 0 AdvA 010203040506 LOCAL_NAME SDR/Bluetooth/Low/Energy
{"pdu_data":"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779","channel":37,"crcinit":"0x555555","accaddr":"0x8E89BED6"}
# Repeat Time
r1000
'''

class LL_Data_Struct:
    def __init__(self,channel,pdu_data,crcinit=0x555555,accaddr = 0x8E89BED6) -> None:
        self.channel = channel
        self.pdu_data = pdu_data
        self.crcinit = crcinit
        self.accaddr = accaddr


def main(top_block_cls=ble_send, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    
    queue_pack = Queue()

    # IF INPUT FILE， PARSE FILE AS JSON

    if len(sys.argv) == 2:
        MODEL = 0
        repeat_time = 0
        index = 0

        packet_file = sys.argv[1]
        packet = open(packet_file,"r")

        for line in packet:
            if "#"  in line[:1] or  "\n" == line[:1]:
                continue
            if "r" in line[:1]:
                repeat_time = int(line[1:])*index
                break
            try:
                data = parse(line=line)
                queue_pack.put(data)
                index +=1
            except:
                print("[Error] JSON Parse Error")
                print (usage)
                break

    # ElSE Listen From Terminal Input / TCP input
    # Devloping...
    else:
        print("TCP Mode < ")
        MODEL = 1
        repeat_time = 0
        '''
        line = sys.stdin.readline()
        data = parse(line)
        queue_pack.put(data)
        '''
        thread_tcp_daemon = threading.Thread(target=Tcp_Daemon,args=(queue_pack,))
        thread_tcp_daemon.setDaemon(True)
        thread_tcp_daemon.start()


    started = False
    #time.sleep(T_IFS*2*0.000001)
    while True:
        if queue_pack.empty()==True:
            #lldata=LL_Data_Struct(37,"E7") #'E7' -> EMPTY FLAG
            lldata=LL_Data_Struct(37,"")
            if MODEL == 0: # Mode 0, the program will automatically exit after sending
                tb.stop()
                os._exit(0)
        else:
            #print (repeat_time)
            lldata = queue_pack.get()
            if repeat_time >= 1:
                queue_pack.put(lldata) #repeat
                repeat_time -=1
        if started == False:
            tb.start()
            started = True
        tb.osmosdr_sink_0.set_center_freq(channel_map[lldata.channel], 0)
        tb.epy_block_0.reset_channel(lldata.channel)
        tb.epy_block_0.reset_pdu_data(lldata.pdu_data)
        tb.epy_block_0.reset_crcinit(lldata.crcinit)
        tb.epy_block_0.reset_accaddr(lldata.accaddr) 
        ## Twice the T_IFS interval to ensure that the contents of the queue will not be lost
        if MODEL == 0:
            time.sleep(T_IFS*2*0.000001) # After testing, the actual accuracy of frequency hopping can only be around 0.01s.
        else :
            #time.sleep(T_IFS*2*0.000001) 
            time.sleep(T_IFS*2*0.001)

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()

'''
Parse the JSON format and write the data into the LL_Data structure
'''
def parse(line):
    packet_data = json.loads(line[:-1])
    channel = packet_data['channel']
    pdu_data = packet_data['pdu_data'].lower()
    try:
        accaddr = int(packet_data['accaddr'],16)
        crcinit = int(packet_data['crcinit'],16)
        if crcinit == 0 :
            print ("empty crcinit")
            crcinit = 0x555555 
        if accaddr == 0:
            print ("empty accaddr")
            accaddr = 0x8E89BED6     
    except:
        accaddr = 0x8E89BED6
        crcinit = 0x555555
    # Store parsed data into LL_Data_Struct
    data = LL_Data_Struct(channel=channel,pdu_data=pdu_data,crcinit=crcinit,accaddr=accaddr)
    return data  

def Tcp_Daemon(queue_pack):
        server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server.settimeout(60)
        #host = '127.0.0.1'
        host = '0.0.0.0'
        port = 52854
        server.bind((host, port))
        server.listen(1) 
        MaxBytes = 2048
        try:
            client,addr = server.accept()          # 等待客户端连接
            print(addr," Device Connected")
            while True:
                data = client.recv(MaxBytes)
                if not data:
                    print('Disconnected')
                    break
                localTime = time.asctime( time.localtime(time.time()))
                print(localTime,' recv bytes num:',len(data))
                print(data.decode())
                try:
                    lldata = parse(data.decode()+"\n")    
                except:
                    print("[Warning] JSON loads Error")
                queue_pack.put(lldata)
        except BaseException as e:
            print("[Error] Socket Error")
            print(repr(e))
        finally:
            server.close()                    # 关闭连接

if __name__ == '__main__':
    main()