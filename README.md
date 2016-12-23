# UDP中继(kcptun)

上行流量用一个UDP，下行流量用另一个UDP，为了缓解ISP封UDP断流问题

需要修改两个py文件中的`端口号`和`服务器地址`

注意：

  --autoexpire 参数需要设置为0, 即取消超时关闭连接, 不然在"stream closed"的时候，会卡住，没有速度，可能是个bug
  

应该还有其它bug
