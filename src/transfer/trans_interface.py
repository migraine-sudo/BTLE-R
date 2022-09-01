
from ble_send import ble_send
from queue import Queue
import sys
import signal
import time

T_IFS = 150


channel_map = {37:2.402e9,38:2.426e9,39:2.480e9,
        0:2.404e9,1:2.406e9,2:2.408e9,3:2.410e9,4:2.412e9,5:2.414e9,6:2.416e9,7:2.418e9,8:2.420e9,9:2.422e9,10:2.424e9,
        11:2.428e9,12:2.430e9,13:2.432e9,14:2.434e9,15:2.436e9,16:2.438e9,17:2.440e9,18:2.442e9,19:2.444e9,20:2.446e9,
        21:2.448e9,22:2.450e9,23:2.452e9,24:2.454e9,25:2.456e9,26:2.458e9,27:2.460e9,28:2.462e9,29:2.464e9,30:2.466e9,
        31:2.468e9,32:2.470e9,33:2.472e9,34:2.474e9,35:2.476e9,36:2.478e9}  # Using tools/chm_gen.py


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
    #data1 = LL_Data_Struct(37,"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779")
    #data2 = LL_Data_Struct(38,"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779")
    #data3 = LL_Data_Struct(39,"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779",crcinit=0x555555,accaddr=0x8E89BED6)
    data1 = LL_Data_Struct(37,'AA')
    data2 = LL_Data_Struct(38,'AABB')
    data3 = LL_Data_Struct(39,'AABBCC')
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