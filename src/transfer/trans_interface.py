
from ble_send import ble_send
from queue import Queue
import sys
import signal
import time

T_IFS = 150

channel_map = {37:2.402e9,38:2.426e9,39:2.480e9}


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
    
    # DEMO
    data1 = LL_Data_Struct(37,"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779")
    data2 = LL_Data_Struct(38,"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779")
    data3 = LL_Data_Struct(39,"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779")
    q = Queue()
    q.put(data1)
    q.put(data2)
    q.put(data3)

    tb.start()
    #time.sleep(T_IFS*2*0.000001)
    while True:
        if q.empty()==True:
            lldata=LL_Data_Struct(37,"")
        else:
            lldata = q.get()
            q.put(lldata) #repeat
        tb.epy_block_0.reset_channel(lldata.channel)
        tb.epy_block_0.reset_pdu_data(lldata.pdu_data)
        tb.epy_block_0.reset_crcinit(lldata.crcinit)
        tb.epy_block_0.reset_accaddr(lldata.accaddr)
        tb.osmosdr_sink_0.set_center_freq(channel_map[lldata.channel], 0)
        ## Twice the T_IFS interval to ensure that the contents of the queue will not be lost
        time.sleep(T_IFS*2*0.000001) # After testing, the actual accuracy of frequency hopping can only be around 0.01s.
        '''
        for i in channel_map:
            #tb.epy_block_0.reset_pdu_data(i)
            tb.epy_block_0.reset_channel(i)
            tb.osmosdr_sink_0.set_center_freq(channel_map[i], 0)
            ## Twice the T_IFS interval to ensure that the contents of the queue will not be lost
            time.sleep(T_IFS*2*0.000001) # After testing, the actual accuracy of frequency hopping can only be around 0.01s.
        '''
        
    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()