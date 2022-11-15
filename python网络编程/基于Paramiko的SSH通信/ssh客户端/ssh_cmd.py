import paramiko


def ssh_command(ip, port, user, passwd, cmd):  # 向SSH服务器发起连接并执行一条命令
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 设置远程服务器没有在know_hosts文件中记录时的应对策略
    client.connect(ip, port=port, username=user, password=passwd)

    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()
    if output:
        print('--- Output ---')
        for line in output:
            print(line.strip())


if __name__ == '__main__':
    import getpass
    # user = getpass.getuser()
    user = input('Username: ')
    password = getpass.getpass()

    ip = input('Enter server IP: ') or '192.168.76.68'
    port = input('Enter port or <CR>: ') or 22
    cmd = input('Enter command or <CR>') or 'id'
    ssh_command(ip, port, user, password, cmd)

