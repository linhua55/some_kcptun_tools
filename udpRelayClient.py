#!/usr/bin/env python
# -*- coding:utf8 -*-
import socket
import select
from time import sleep
import queue


clientRelayPort = 3389  # client bind port, need modify
serverOutboundPort = 3391
serverInboundPort = 3387
server = 'xxx.xxx.xxx.xxx'  # your server ip

serverInbound = (server, serverInboundPort)
serverOutbound = (server, serverOutboundPort)

buffer = 32768



class UdpRelayClient(object):
    def udpRelayClient(self):
        outBytes = 0

        clientSocketRelay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientSocketRelay.bind(('', clientRelayPort))
        clientSocketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientSocketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        message_queues = {}
        message_queues[clientSocketOut] = queue.Queue()
        message_queues[clientSocketIn] = queue.Queue()
        message_queues[clientSocketRelay] = queue.Queue()
        while True:
            sleep(0.001)
            self.ready_socks, self.writable_socks, _ = select.select([clientSocketRelay, clientSocketIn], [clientSocketOut, clientSocketRelay], [])
            for sock in self.ready_socks:
                if sock.fileno() == clientSocketRelay.fileno():
                    try:
                        recvData, (localAddress, localPort) = sock.recvfrom(buffer)
                    except ConnectionError:
                        clientSocketOut = self.recreateSocket(clientSocketOut, message_queues)
                    except:
                        continue
                    else:
                        if recvData:
                            message_queues[clientSocketOut].put(recvData)
                        else:
                            # TODO
                            clientSocketOut = self.recreateSocket(clientSocketOut, message_queues)

                elif sock.fileno() == clientSocketIn.fileno():
                    backRecvData = sock.recv(buffer)
                    if backRecvData:
                        message_queues[clientSocketRelay].put(backRecvData)


            for sock in self.writable_socks:
                if sock is clientSocketOut:
                    try:
                        next_msg = message_queues[sock].get_nowait()
                    except:
                        continue
                    else:
                        outBytes = outBytes + len(next_msg)
                        sock.sendto(next_msg, serverInbound)
                        clientSocketIn.sendto(b"", serverOutbound)
                        # print(clientSocketIn.getsockname())
                elif sock is clientSocketRelay:
                    try:
                        next_msg = message_queues[sock].get_nowait()
                    except:
                        continue
                    else:
                        sock.sendto(next_msg, (localAddress, localPort))

            # if outBytes > 10M, change a sending port.  outBytes == serverInboundBytes
            if outBytes > 10*1024*1024:
                outBytes = 0
                clientSocketOut = self.recreateSocket(clientSocketOut, message_queues)

        clientSocketOut.close()
        clientSocketIn.close()
        clientSocketRelay.close()


    def recreateSocket(self, socketName, message_queues):
        socketName1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message_queues[socketName1] = message_queues[socketName]
        # in order to destroy the socket, delete the corresponding message_queue first
        del message_queues[socketName]
        socketName.close()
        return socketName1

if __name__ == '__main__':
    udpRelayClient = UdpRelayClient()
    udpRelayClient.udpRelayClient()

