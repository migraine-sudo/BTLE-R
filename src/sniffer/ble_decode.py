#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: migraine
# GNU Radio version: 3.8.5.0

from gnuradio import blocks
from gnuradio import digital
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import epy_block_0
import epy_block_1
import epy_block_2
import osmosdr
import time


class ble_decode(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 4e6
        self.freq_channel = freq_channel = 2.402e9
        self.crc_init = crc_init = '0x555555'
        self.channel_id = channel_id = 37
        self.access_address = access_address = '0x8E89BED6'

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_pub_msg_sink_0 = zeromq.pub_msg_sink('tcp://*:52855', 0, True)
        self.osmosdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + ""
        )
        self.osmosdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(freq_channel, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(True, 0)
        self.osmosdr_source_0.set_gain(10, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(2e6, 0)
        self.epy_block_2 = epy_block_2.blk(CHANNEL=channel_id, CRCINIT=crc_init, ADVADDRESS='')
        self.epy_block_1 = epy_block_1.blk(CHANNEL=channel_id)
        self.epy_block_0 = epy_block_0.blk(AA=access_address)
        self.digital_gfsk_demod_0 = digital.gfsk_demod(
            samples_per_symbol=4,
            sensitivity=0.392699,
            gain_mu=0.175,
            mu=0.5,
            omega_relative_limit=0.005,
            freq_error=0.0,
            verbose=False,
            log=False)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate,True)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0, 'msg_out'), (self.epy_block_1, 'msg_in'))
        self.msg_connect((self.epy_block_1, 'msg_out'), (self.epy_block_2, 'msg_in'))
        self.msg_connect((self.epy_block_2, 'msg_out'), (self.zeromq_pub_msg_sink_0, 'in'))
        self.connect((self.blocks_throttle_0, 0), (self.digital_gfsk_demod_0, 0))
        self.connect((self.digital_gfsk_demod_0, 0), (self.epy_block_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.blocks_throttle_0, 0))


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)

    def get_freq_channel(self):
        return self.freq_channel

    def set_freq_channel(self, freq_channel):
        self.freq_channel = freq_channel
        self.osmosdr_source_0.set_center_freq(self.freq_channel, 0)

    def get_crc_init(self):
        return self.crc_init

    def set_crc_init(self, crc_init):
        self.crc_init = crc_init

    def get_channel_id(self):
        return self.channel_id

    def set_channel_id(self, channel_id):
        self.channel_id = channel_id

    def get_access_address(self):
        return self.access_address

    def set_access_address(self, access_address):
        self.access_address = access_address





def main(top_block_cls=ble_decode, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    main()
