# some_kcptun_tools
some kcptun relevant tools

需要修改两个py文件中的`端口号`和`服务器地址`

注意：
  --autoexpire 参数需要设置为0, 即取消超时关闭连接, 不然在"stream closed"的时候，会卡住，没有速度，可能是个bug
