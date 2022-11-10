import argparse  # 创建一个带命令行界面的程序
import socket
import shlex
import subprocess  # 进程创建接口
import sys
import textwrap
import threading


def execute(cmd):
    """
    执行一条bash指令
    :param cmd: 执行指令的名称
    :return: 执行指令后返回的结果
    """
    cmd = cmd.strip()
    if not cmd:
        return
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)  # 创建一个新进程以执行一条指令，并返回执行指令后的结果
    return output.decode()


class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建一个socket对象
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response, end="")
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print('User terminated.')
            self.socket.close()
            sys.exit()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))  # self.args.target: 命令行选项-t后跟的参数
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

    def handle(self, client_socket):
        """
        服务端的一些选项以及对应的操作
        :param client_socket:  客户端socket
        :return:
        """
        if self.args.execute:  # 为客户端提供一条指令的执行
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        elif self.args.upload:  # 为客户端提供文件upload
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break

            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())

        elif self.args.command:  # 为客户端提供一个交互式shell
            cmd_buffer = b''
            flag = False  # 用于第一次给客户端发送<BHP: #
            while True:
                try:
                    if not flag:
                        client_socket.send(b'<BHP: #')
                        flag = True
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    response += '<BHP: #'
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()

    def run(self):
        if self.args.listen:
            self.listen()  # 服务端接口
        else:
            self.send()  # 客户端接口


if __name__ == '__main__':
    # 命令行终端的一些选项,以及客户端、服务端的分离
    parser = argparse.ArgumentParser(
        description='BHP NET Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
            netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
            netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
            netcat.py -t 192.168.1.108 -p 5555 # connect to server
        ''')
    )
    parser.add_argument('-c', '--command', action='store_true', help='command shell')  # action='store_true'表示带上-c选项时value为true，执行该py文件时，调用command方法;不带-c选项的话，则value为false，不调用command方法
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')
    args = parser.parse_args()
    if args.listen:  # 服务端选项
        buffer = ''
    else:  # 客户端选项
        buffer = sys.stdin.read()  # 标准输入，表示等待从终端输入  按ctrl+z可代表输入EOF,结束输入

    nc = NetCat(args, buffer.encode())
    nc.run()



