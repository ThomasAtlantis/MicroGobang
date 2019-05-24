import socket
import time

sock = conn = None
SERVER_SOCKET = ("192.168.1.109", 8000)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(SERVER_SOCKET)  # 绑定服务器socket
sock.settimeout(None)  # 超时时间无限长
sock.listen(10)  # 最大连接数
try:
	while True:
	    conn, addr = sock.accept()  # 阻塞，等待客户端接入
	    conn.settimeout(None)
	    while True:
	        szBuf = conn.recv(1024) # 阻塞，等待客户端发送消息
	        print(szBuf.decode("utf-8"))
except:
	if sock: sock.close()
	if conn: conn.close()