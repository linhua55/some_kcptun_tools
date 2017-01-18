# For Linux - Sniffs all incoming and outgoing packets :)

import socket, sys
from struct import *

udpDstPort = 3389
tcpDstPort = 441
serverIP = 'xxx.xxx.xxx.xxx'
udpDstAddr = ('127.0.0.1', udpDstPort)

natDict = dict() # for NAT/NAPT function
tcpSrcAddr = ('127.0.0.1', 441)

# checksum functions needed for calculation checksum
def checksum_m(msg):
    s = 0

    # if len(msg) is odd
    if len(msg)%2 ==1:
        msg = msg + b'\0'

    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        # w = ord(msg[i]) + (ord(msg[i + 1]) << 8)
        w = (msg[i]) + ((msg[i + 1]) << 8)
        s = s + w

    s = (s >> 16) + (s & 0xffff)
    s = s + (s >> 16)

    # complement and mask to 4 byte short
    s = ~s & 0xffff

    return s

# Convert a string of 6 characters of ethernet address into a dash separated hex string
def eth_addr(a):
    b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (a[0], a[1], a[2], a[3], a[4], a[5])
    return b


# create a AF_PACKET type raw socket (thats basically packet level)
# define ETH_P_ALL    0x0003          /* Every packet (be careful!!!) */
try:
    s_recv = socket.socket(socket.AF_PACKET, socket.SOCK_DGRAM, socket.ntohs(0x0800)) # socket.SOCK_RAW
except socket.error as msg:
    print('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

# create a raw socket
try:
    s_send_tcp = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
except socket.error as msg:
    print('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

s_send_tcp.bind(('', tcpDstPort))

try:
    s_send_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as msg:
    print('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

# receive a packet
while True:
    packet = s_recv.recvfrom(65565)

    interface = packet[1][0]  # lo
    # if interface != 'venet0':
    #     print(interface)
    #     print("packet: ", "".join("%02x" % b for b in packet[0]))

    # packet string from tuple
    packet = packet[0]

    # print("packet: ", "".join("%02x" % b for b in packet))

    eth_length = 0

    # Parse IP packets, IP Protocol number = 8
    # Parse IP header
    # take first 20 characters for the ip header
    ip_header = packet[eth_length:20 + eth_length]

    # now unpack them :)
    iph = unpack(b'!BBHHHBBH4s4s', ip_header)

    version_ihl = iph[0]
    version = version_ihl >> 4
    ihl = version_ihl & 0xF

    iph_length = ihl * 4

    ttl = iph[5]
    protocol = iph[6]
    s_addr = socket.inet_ntoa(iph[8])
    d_addr = socket.inet_ntoa(iph[9])

    # print('Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(ttl) + ' Protocol : ' + str(
    #     protocol) + ' Source Address : ' + str(s_addr) + ' Destination Address : ' + str(d_addr))

    # TCP protocol
    if protocol == 6:
        t = iph_length + eth_length
        tcp_header = packet[t:t + 20]

        # now unpack them :)
        tcph = unpack(b'!HHLLBBHHH', tcp_header)

        source_port = tcph[0]
        dest_port = tcph[1]
        sequence = tcph[2]
        acknowledgement = tcph[3]
        doff_reserved = tcph[4]
        tcph_length = doff_reserved >> 4

        if dest_port == tcpDstPort:
            # print('Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(ttl) + ' Protocol : ' + str(
            #     protocol) + ' Source Address : ' + str(s_addr) + ' Destination Address : ' + str(d_addr))
            # print('Source Port : ' + str(source_port) + ' Dest Port : ' + str(dest_port) + ' Sequence Number : ' + str(
            #     sequence) + ' Acknowledgement : ' + str(acknowledgement) + ' TCP header length : ' + str(tcph_length))

            # ip_header_send = ip_header[0:12] + pack(b'!4s4s', iph[9], iph[8]) + packet[20:t]
            # packet_send = ip_header_send + pack(b'!HH', dest_port, source_port) + packet[t+4:]
            # s_send.sendto(packet_send, (s_addr, 0))

            h_size = eth_length + iph_length + tcph_length * 4
            # data_size = len(packet) - h_size

            # get data from the packet
            data = packet[h_size:]

            # print('Data : ' + str(data))

            OldTcpSrcAddr = tcpSrcAddr
            tcpSrcAddr = (s_addr, source_port)

            if OldTcpSrcAddr != tcpSrcAddr:
                s_send_udp.close()
                try:
                    s_send_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                except socket.error as msg:
                    print('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
                    sys.exit()
            s_send_udp.sendto(data, udpDstAddr)

            # need to implement NAT/NAPT function
            # “assigning a name to a socket”  http://man7.org/linux/man-pages/man2/bind.2.html
            _ , s_port = s_send_udp.getsockname()
            natDict.update(dict([(s_port, tcpSrcAddr)]))

    # UDP packets
    elif protocol == 17:
        u = iph_length + eth_length
        udph_length = 8
        udp_header = packet[u:u + 8]

        # now unpack them :)
        udph = unpack(b'!HHHH', udp_header)

        source_port = udph[0]
        dest_port = udph[1]
        length = udph[2]
        checksum = udph[3]

        if interface == 'lo' and source_port == udpDstPort:

            # print('Source Port : ' + str(source_port) + ' Dest Port : ' + str(dest_port) + ' Length : ' + str(
            #     length) + ' Checksum : ' + str(checksum))

            h_size = eth_length + iph_length + udph_length
            # data_size = len(packet) - h_size

            # get data from the packet
            data = packet[h_size:]
            # data = udp_header + data

            # print('Data : ' + str(data))

            if dest_port in natDict:
                tcpSrcAddr = natDict.get(dest_port)  # can't remove(maybe one packet in, some packets out) natDict.pop(dest_port)
            else:
                continue

            # tcp header fields
            tcp_source = tcpDstPort  # source port
            tcp_dest = tcpSrcAddr[1] # destination port
            tcp_seq = 454
            tcp_ack_seq = 0
            tcp_doff = 5  # 4 bit field, size of tcp header, 5 * 4 = 20 bytes
            # tcp flags
            tcp_fin = 0
            tcp_syn = 1
            tcp_rst = 0
            tcp_psh = 0
            tcp_ack = 0
            tcp_urg = 0
            tcp_window = socket.htons(5840)  # maximum allowed window size
            tcp_check = 0
            tcp_urg_ptr = 0

            tcp_offset_res = (tcp_doff << 4) + 0
            tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh << 3) + (tcp_ack << 4) + (tcp_urg << 5)

            # the ! in the pack format string means network order
            tcp_header = pack(b'!HHLLBBHHH', tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,
                              tcp_window,
                              tcp_check, tcp_urg_ptr)

            # user_data = b'GET / HTTP/1.1\r\n\r\n'
            # b'GET /index.html HTTP/1.1\r\nHost:  www.baidu.com\r\n\r\n'

            # pseudo header fields
            source_address = socket.inet_aton(serverIP)
            dest_address = socket.inet_aton(tcpSrcAddr[0])
            placeholder = 0
            protocol = socket.IPPROTO_TCP
            tcp_length = len(tcp_header) + len(data)

            psh = pack(b'!4s4sBBH', source_address, dest_address, placeholder, protocol, tcp_length)
            psh = psh + tcp_header + data

            tcp_check = checksum_m(psh)
            # print tcp_checksum

            # make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
            tcp_header = pack(b'!HHLLBBH', tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,
                              tcp_window) + pack(
                b'H', tcp_check) + pack(b'!H', tcp_urg_ptr)

            # final full packet - syn packets dont have any data
            packet = tcp_header + data

            # Send the packet finally - the port specified has no effect
            s_send_tcp.sendto(packet, (tcpSrcAddr[0], 0))  # put this in a loop if you want to flood the target
