# BTLE-R

![](https://img.shields.io/badge/Hardware-Hackrf%20One-brightgreen)![](https://img.shields.io/badge/Protocol-BLE-blue)

**BTLE-Radio** is an open source software-defined radio (HackRF One) Bluetooth low energy software experiment kit. Implement BLE baseband using software definition. In the BLE protocol stack, it corresponds to the physical layer and the link layer.

Currently supports sniffing and parsing of air interface packets in three frequency bands, so stay tuned!

> Refer to Bluetooth Core Specification v 5.3

# Requirements

Tested runtime environment  *(but not required)* :

- [gnuradio](https://github.com/gnuradio/gnuradio) v*3.8.5.0*
- [gr-osmosdr](https://github.com/osmocom/gr-osmosdr) v*0.2.0.0*
- [HackRF One](https://github.com/greatscottgadgets/hackrf) with firmware 2021.03.1

# BUILD&RUN

Install the HackRF driver and GNURadio components, and the default firmware of HACKRF ONE can be used.

## OSX

There are many OSX installation problems, it is recommended to upgrade macport to the latest version. My test environment is OSX12.4.

Install hackrf driver

```shell
sudo port install hackrf
```

The GNURadio suite can be installed using the command, but it is recommended to download and install the [DMG version](https://github.com/ktemkin/gnuradio-for-mac-without-macports/releases).

```shell
sudo port install gnuradio
```

To use HackRF One on OSX platform, additionally install gr-osmosdr for GNURadio

```shell
sudo port install gr-osmosdr
```

## Ubuntu

Compile the hackrf driver

```shell
cd ~/hackrf_files && git clone https://github.com/mossmann/hackrf.git
cd ~/hackrf_files/hackrf/host && mkdir build && cd build && cmake .. && make && sudo make install && sudo ldconfig
```

Install GNURadio Suite

```shell
 sudo aptitude install gnuradio
```

run gnuradio companion

```shell
sudo gnuradio-companion
```

## RUN

1. Run GRC. The flow chart is mainly used to develop and debug BTLE-R. You can manually set the frequency band, AccessAddress, etc. in the parameters. If you need to perform automatic channel selection and connection tracking, please use BTLE-R directly.

   To run the flow graph in GNURadioCompanion or run the python script ble_decode.py, use the following command.

```shell
$ python3 ble_decode.py
```

![BLE_ADV_Capture](./pic/BLE_ADV_Capture.png)

2. Run BTLE-R (in development). Use python to customize the baseband logic, and currently can complete the frequency hopping of the broadcast channel.

```shell
$ python3 BTLE-R.py
```



# Doc

![GRC-Sniffer](./pic/GRC-Sniffer.png)Moudle Design

- GFSKDemod (GNURadio Default)

- BlE Packets Gain

- Data Whiting/De-Whiting

- CRC Check
- PDU Parse(Only Advertising Physical Channel，so far)

In the Plan

- Data Physical Channel

- Hop channel
- Transfer Mode(big project，maybe another)
