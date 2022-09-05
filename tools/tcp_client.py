import socket
import time

host ='127.0.0.1'
port = 52854
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.settimeout(30)

client.connect((host,port))

#list = ['{"pdu_data":"2025f65a9c83e5c10201061bff570102ffffffffffffffffffffffffffffffff03c1e5839c5af6","channel":37,"crcinit":"0x555555","accaddr":"0x8E89BED6"}']
#list =  ['{"pdu_data":"6025727919bebae70201061bff570102ffffffffffffffffffffffffffffffff03e7babe197972","channel":37,"crcinit":"0x555555","accaddr":"0x8E89BED6"}']
#list =  ['{"pdu_data":"6025727919bebae70201061bff570102ffffffffffffffffffffffffffffffff03e7babe197972","channel":37,"crcinit":"0x555555","accaddr":"0x8E89BED6"}']
#list = ['{"pdu_data":"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779","channel":37,"crcinit":"0x555555","accaddr":"0x8E89BED6"}']

list = ['{"pdu_data":"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779","channel":37,"crcinit":"0x555555","accaddr":"0x8E89BED6"}',
        '{"pdu_data":"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779","channel":38,"crcinit":"0x555555","accaddr":"0x8E89BED6"}',
        '{"pdu_data":"022006050403020119095344522f426c7565746f6f74682f4c6f772f456e65726779","channel":39,"crcinit":"0x555555","accaddr":"0x8E89BED6"}'  
]




while True:
    for i in list:
        inputData=i+"\n"
        time. sleep(0.01)
        #if(inputData=="quit"):
        #    print("Quiting...")
        #    break
        sendBytes = client.send(inputData.encode())
client.close()
