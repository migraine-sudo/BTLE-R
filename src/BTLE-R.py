import sys
sys.path.append('./sniffer/')

from bisect import bisect_left
from pickle import TRUE

import ble_decode
import signal
import sys
import time

"""
The RADIO module controller controls the BLE baseband written by GNURadio. 
Support frequency hopping, BLE air interface unpacking, etc.
"""
class RADIO:
    def __init__(self,tb) -> None:
        self.tb=tb
        self.sniff_adv_on = False
        
    def HopChannel(self,channel,crcint='0x555555'):
        freq = self.channel_map[channel]
        self.tb.set_freq_channel(freq)
        self.tb.epy_block_1.reset_channel(channel)
        self.tb.epy_block_2.reset_channel(channel)
    channel_map = {37:2.402e9,38:2.426e9,39:2.480e9}

    def sniff_adv(self):
        # Adv Phy
        self.sniff_adv_on = True
        while self.sniff_adv_on:
            for c in [37,38,39]:
                self.HopChannel(c)
                time.sleep(0.55)    

def main(top_block_cls=ble_decode.ble_decode, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    
    tb.start()
    
    radio = RADIO(tb)
    radio.sniff_adv()

    tb.wait()
    

if __name__ == '__main__':
    main()