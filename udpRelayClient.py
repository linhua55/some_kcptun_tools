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
        inBytes = 0

        clientSocketRelay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientSocketRelay.bind(('', clientRelayPort))
        clientSocketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientSocketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientSocketIn2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        message_queues = {}
        message_queues[clientSocketOut] = queue.Queue()
        message_queues[clientSocketRelay] = queue.Queue()
        while True:
            sleep(0.001)
            # TODO timeout parameter  When message_queues is null, execute this(only InSocket), to reduce cpu usage
            self.ready_socks, self.writable_socks, _ = select.select([clientSocketRelay, clientSocketIn2, clientSocketIn], [clientSocketOut, clientSocketRelay], [])
            # self.ready_socks = None
            # if message_queues[clientSocketOut].qsize() == 0 or message_queues[clientSocketRelay].qsize() == 0:
            #     self.ready_socks, self.writable_socks, _ = select.select([clientSocketRelay, clientSocketIn, clientSocketIn2], [clientSocketOut, clientSocketRelay], [])
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

                # resolve the reside traffic when clientSocketIn changed(change port)
                # before clientSocketIn(Wrong!!!not useful)
                elif sock.fileno() == clientSocketIn2.fileno():
                    backRecvData = sock.recv(buffer)
                    if backRecvData:
                        message_queues[clientSocketRelay].put(backRecvData)

                elif sock.fileno() == clientSocketIn.fileno():
                    backRecvData = sock.recv(buffer)
                    if backRecvData:
                        message_queues[clientSocketRelay].put(backRecvData)
                        inBytes = inBytes + len(backRecvData)



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

            # if outBytes > 5M, change a sending port.  outBytes == serverInboundBytes
            if outBytes > 5*1024*1024:
                outBytes = 0
                clientSocketOut = self.recreateSocket(clientSocketOut, message_queues)

            #  DONE !!!need to check whether or not the clientSocketIn have data to be read!!!
            #  and (clientSocketIn not in self.ready_socks)
            # if inBytes > 10M, chang a port  !! Control the traffic or control the speed
            if inBytes > 10*1024*1024:
                inBytes = 0
                clientSocketIn2 = clientSocketIn
                clientSocketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        clientSocketOut.close()
        clientSocketIn.close()
        clientSocketIn2.close()
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

