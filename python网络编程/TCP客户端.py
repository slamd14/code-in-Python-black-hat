import socket

target_host = '127.0.0.1'
target_port = 9998

# 建立一个 socket 对象（参数 AF_INET 表示标准 IPv4 地址或主机名，SOCK_STREAM 表示 TCP 客户端）
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 将客户端连接到服务器
client.connect((target_host, target_port))

# 向服务器发送数据
client.send(b"hello, my TCP server")

# 接收返回的数据
response = client.recv(4096)

# 打印返回数据
print(response.decode())
client.close()