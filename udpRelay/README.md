# UDP中继(kcptun)

为了缓解ISP封UDP断流问题

1. 上行流量和下行流量分别用不同的UDP端口，

2. 设置流量上限 来 触发 更换 客户端发送和接收端口

需要修改两个py文件中的`端口号`和`服务器地址`，见下

python3程序

注意：

1. --autoexpire 参数需要设置为0, 即取消超时关闭连接, 不然在"stream closed"的时候，会卡住，没有速度，可能是个bug

~~2. 只单独重启一端会卡住，需要先关闭客户端和服务端，再重启~~

3. cpu占用率有点高，应该是个bug

4. 应该还有其它bug

# 使用方法

在使用前需要修改参数

## udpRelayServer.py

打开udpRelayServer.py文件，里面的几个参数：

1. serverInboundPort: 用来传输 上行流量 的服务器监听端口

2. serverOutboundPort: 用来传输 下行流量 的服务器监听端口

3. kcptunBindPort: kcptun服务器端监听端口

## udpRelayClient.py

打开udpRelayClient.py文件，里面的几个参数：

1. clientRelayPort: 客户端监听端口，kcptun客户端设置的服务器地址需要和此一致，即("127.0.0.1", clientRelayPort)。一般设置成和kcptun服务器端的监听端口(kcptunBindPort)一致。

2. serverOutboundPort: 用来传输 下行流量 的服务器监听端口

3. serverInboundPort: 用来传输 上行流量 的 服务器监听端口

4. server：服务器IP地址

## 运行

服务端运行udpRelayServer.py文件

    $ python3 udpRelayServer.py

客户端运行udpRelayClient.py文件

    $ python3 udpRelayClient.py


