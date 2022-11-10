import sys
import socket
import threading

# 在所有可打印的字符的位置上，保持原有的字符不变;在所有不可打印字符的位置上，放一个'.'
# 这有助于理解未知协议的格式，或是在明文协议里查找用户的身份凭证等
HEX_FILTER = ''.join([(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])


def hexdump(src, length=16, show=True):
    """
    把本地和远程设备之间的通信过程显示到屏幕上
    :param src: 传入的数据
    :param length: 输出格式控制
    :param show: 是否输出通信过程到屏幕
    :return: 格式化后的src数据
    """
    if isinstance(src, bytes):
        src = src.decode(errors='replace')  # 尝试代理ssh的时候遇到了解码错误问题(因为ssh是加密通信)，加上errors='replace放宽解码要求

    results = list()
    for i in range(0, len(src), length):
        word = str(src[i:i+length])
        printable = word.translate(HEX_FILTER)  # 在所有可打印的字符的位置上，保持原有的字符不变;在所有不可打印字符的位置上，放一个'.'
        hexa = ' '.join([f'{ord(c)}:02x' for c in word])
        hexwidth = length * 3
        results.append(f'{i:04x}  {hexa:<{hexwidth}}  {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results


def receive_from(connection):
    """
    从代理两端接收数据
    :param connection: socket对象
    :return: 将buffer返回给调用方
    """
    buffer = b""  # 存储socket对象返回的数据
    connection.settimeout(5)  # 超时时间默认为5秒，如果跨国转发流量，或者网络状况很差的话，5s可能不太合适  # 阻塞5s
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer


def request_handler(buffer):
    # perform packet modifications
    # 在这些函数里，可以修改数据包内容，进行模糊测试，挖掘权限校验漏洞，做你想做的任何事
    return buffer


def response_handler(buffer):
    # perform packet modifications
    # 在这些函数里，可以修改数据包内容，进行模糊测试，挖掘权限校验漏洞，做你想做的任何事
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    """
    处理代理转发逻辑(收发数据流两端的数据):
    1. 从客户端接收数据，对数据进行处理，转发到服务端
    2. 从服务端接收数据，对数据进行处理，转发到客户端
    3. 同时断开与客户端、服务端连接
    :param client_socket:
    :param remote_host:
    :param remote_port:
    :param receive_first: 确定是否需要从服务器那边先接收一段数据
    :return:
    """
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    remote_buffer = ''
    if receive_first:  # 确定是否需要从服务器那边先接收一段数据，有的服务器会要求你做这样的操作
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

    remote_buffer = response_handler(remote_buffer)
    if len(remote_buffer):
        print("[<==] Sending %d bytes to localhost." % len(remote_buffer))
        client_socket.send(remote_buffer)

    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            line = "[==>] Received %d bytes from localhost." % len(local_buffer)
            print(line)
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")

        if len(local_buffer) == 0 and len(remote_buffer) == 0:
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections")
            break


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    # 用来创建和管理连接
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print('problem on bind: %r' % e)

        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    print("[*] Listening on %s:%d" % (local_host, local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # print out the local connection information
        line = "> Received incoming connection from %s:%d" % (addr[0], addr[1])
        print(line)
        # start a thread to talk to the remote host
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first)
        )
        proxy_thread.start()


def main():
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end='')
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


if __name__ == '__main__':
    main()
