# UDP to TCP 中继(kcptun)

为了解决ISP封UDP断流问题，利用raw socket(pcap也行)将UDP流量通过TCP进行中继

python3程序

注意：

  1. 不能在Windows上，只能在Linux下。在Windows上可以使用Linux虚拟机运行，但是Linux虚拟机必须使用 桥接网卡 方式访问外部网络，不能使用 NAT方式 访问外部网络

  2. 为了防止卡住，更换一端的kcptun参数后，先关闭两端(server/client)的kcptun，然后依次运行服务端kcptun和客户端kcptun

# 使用方法

在使用前需要修改参数，并设置iptables规则

## 设置iptables规则，禁止内核对TCP流量的处理(kernel bypass for TCP/IP stack)

### 服务端

      iptables -A INPUT -p tcp --destination-port <your_TCP_bind_port> -j DROP

### 客户端

      iptables -A INPUT -s <your_server_ip> -p tcp --sport <your_TCP_bind_port> -j DROP

## 修改参数
### relayRawSocketClient.py 中

  1. udpDstPort：kcptun服务端的UDP监听端口
  2. tcpDstPort: 本程序服务端的TCP监听端口(可任意，但两个文件中的需一致)，即上文中的<your_TCP_bind_port>
  3. serverIp: VPS服务器的IP地址，即上文中的<your_server_ip>

### relayRawSocketServer.py 中

  1. udpDstPort：kcptun服务端的UDP监听端口
  2. tcpDstPort: 本程序服务端的TCP监听端口(可任意，但两个文件中的需一致)，即上文中的<your_TCP_bind_port>
  3. serverIp: VPS服务器的IP地址，即上文中的<your_server_ip>
