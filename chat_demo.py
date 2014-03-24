#!/usr/bin/python
#coding=utf-8

import os
import sys
import time
import json
import getopt
import socket
import select
import fcntl
import thread
from datetime import datetime


BLOCK_SIZE = 1024
now = datetime.now

def log(fmt='', *args):
    time = '%s | ' % now()
    msg = fmt % args
    print(time + msg)

# 将文件描述符设置为不阻塞
def setnoblock(filepointer):
    fd = filepointer.fileno()
    val = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, val | os.O_NONBLOCK)

def send_boardcast(host, port):
    """
    广播服务器的ip地址和端口，以便客户端连接上来
    """
    msg = '%s:%s' % (host, port)
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
    while True:
        try:
            server.sendto(msg, ('<broadcast>', port))
            time.sleep(0.5)
        except socket.error:
            break
    server.close()

def recv_boardcast(host, port):
    """
    接收服务器的广播消息
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(('', port))
    client.settimeout(2)
    try:
        msg, addr = client.recvfrom(BLOCK_SIZE)
    except socket.timeout:
        msg = None
    client.close()
    return msg


def start_server(host, port):
    # 设置监听套接字
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    server.setblocking(False)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except:
        pass
    log('listen on %s:%d', host, port)

    thread.start_new_thread(send_boardcast, (host, port))

    clients = set()
    def close_client(conn):
        clients.discard(conn)
        conn.close()

    while True:
        lclients = list(clients)
        # ready
        rinputs, routputs, rexcept = select.select([server] + lclients, lclients, [])
        for conn in rinputs:
            # 如果是监听套接字
            if conn == server:
                conn, addr = server.accept()
                clients.add(conn)
                log('%s:%s joined', addr[0], addr[1])
            # 如果是客户端套接字
            else:
                try:
                    data = conn.recv(BLOCK_SIZE)
                except socket.error:
                    close_client(conn)
                    break
                remote_ip, port = conn.getpeername()
                # 如果客户端关闭连接
                if not data:
                    log('%s:%s exited', remote_ip, port)
                    close_client(conn)
                    break
                # 将消息包装成JSON并发送给所有客户端
                msg = json.dumps({
                    'user': '%s:%s' % (remote_ip, port),
                    'time': str(now()),
                    'data': data,
                })
                for client in routputs:
                    if client == conn:
                        continue
                    client.send(msg)
                # 输出聊天记录到控制台
                log('%s:%s send `%s`', remote_ip, port, data)


def start_client(host, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    client.setblocking(False)
    setnoblock(sys.stdin)
    inputs = [client, sys.stdin]
    log('connect %s:%d success', host, port)

    while True:
        rinputs, routputs, rexcept = select.select(inputs, [], [])
        for fin in rinputs:
            if fin == client:
                data = client.recv(BLOCK_SIZE)
                # 如果服务器关闭连接
                if not data:
                    log('server closed')
                    client.close()
                    return
                msg = json.loads(data)
                # 处理字符编码
                if not isinstance(msg['data'], unicode):
                    msg['data'] = msg['data'].decode('utf-8')
                # 输出消息到控制台，封装成函数会好点
                print(msg['time'] + '\t' + msg['user'])
                print(msg['data'])
            elif fin == sys.stdin:
                try:
                    data = raw_input()
                    if len(bytes(data)) > BLOCK_SIZE:
                        log('message length exceed')
                        continue
                    client.send(data)
                except EOFError:
                    log('exit')
                    client.close()
                    return


def main():
    # 公网ip
    hostname = socket.getfqdn(socket.gethostname())
    host = socket.gethostbyname(hostname)
    port = 8888
    is_server = None
    is_client = None

    try:
        # 从命令行读取参数
        opts, args = getopt.getopt(sys.argv[1:], "CSH:p:", ["host=","port="])
        for opt, val in opts:
            if opt in ('-H', '--host'):
                host = val
            elif opt in ('-p', '--port'):
                port = int(val)
            # 以服务器的方式启动
            elif opt in ('-S', '--server'):
                is_server = True
            # 以客户端的方式启动
            elif opt in ('-C', '--client'):
                is_client = True
    except getopt.GetoptError as e:
        pass

    if is_server:
        start_server(host, port)
    elif is_client:
        start_client(host, port)
    else:
        # 广播查询是否存在可用服务器
        addr = recv_boardcast(host, port)
        if addr:
            host, port = addr.split(':')
            start_client(host, int(port))
        else:
            start_server(host, port)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
