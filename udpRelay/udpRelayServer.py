#!/usr/bin/env python
# -*- coding:utf8 -*-
from time import sleep
from collections import deque
import socket
import select

serverInboundPort = 3387
serverOutboundPort = 3391
kcptunBindPort = 3389

kcptunBind = ('127.0.0.1', kcptunBindPort)

buffer = 32768



class UdpRelayServer:
    def udpRelayServer(self):

        # receive the inbound flow
        self.socketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketIn.bind(('', serverInboundPort))
        # outbound flow
        self.socketRelay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # obtain the remoteAddress, remotePort  from the empty packet which is sent to the port serverOutboundPort
        # And send packet from port serverOutboundPort
        self.socketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketOut.bind(("", serverOutboundPort))

        message_queues = {}
        message_queues[self.socketRelay] = deque()
        message_queues[self.socketOut] = deque()

        while True:
            sleep(0.001)
            self.ready_socks, self.writable_socks, _ = select.select([self.socketOut, self.socketIn, self.socketRelay], [self.socketRelay, self.socketOut], [])
            for sock in self.ready_socks:
                if sock.fileno() == self.socketOut.fileno():
                    _, (remoteAddress, remotePort) = sock.recvfrom(1024)
                elif sock.fileno() == self.socketIn.fileno():
                    try:
                        self.recvdata = sock.recv(buffer)
                    # except ConnectionError:  # handle the exception that the client close the connection(udp don't have)
                    #     self.socketRelay = self.recreateSocket(self.socketRelay, message_queues)
                    except:
                        continue
                    else:
                        if self.recvdata:
                            # kcptun bind port kcptunBindPort
                            message_queues[self.socketRelay].append(self.recvdata)
                        # else:
                        #     # TODO
                        #     # client hang up?
                        #     self.socketRelay = self.recreateSocket(self.socketRelay, message_queues)

                elif sock.fileno() == self.socketRelay.fileno():
                    self.recvrelaydata, _ = sock.recvfrom(buffer)
                    if self.recvrelaydata:
                        message_queues[self.socketOut].append(self.recvrelaydata)

            for sock in self.writable_socks:
                if sock is self.socketRelay:
                    try:
                        next_msg = message_queues[sock].popleft()
                    except:
                        continue
                    else:
                        sock.sendto(next_msg, kcptunBind)
                elif sock is self.socketOut:
                    try:
                        next_msg = message_queues[sock].popleft()
                    except:
                        continue
                    else:
                        sock.sendto(next_msg, (remoteAddress, remotePort))

        self.socketIn.close()
        self.socketOut.close()
        self.socketRelay.close()

    def recreateSocket(self, socketName, message_queues):
        socketName1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # use deque, as queue.Queue can't be copy
        message_queues[socketName1] = message_queues[socketName].copy()
        del message_queues[socketName]
        socketName.close()
        return socketName1


if __name__ == '__main__':
    udpRelayServer = UdpRelayServer()
    udpRelayServer.udpRelayServer()
