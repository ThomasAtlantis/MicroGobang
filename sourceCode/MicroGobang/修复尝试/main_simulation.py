import socket
import json
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.connect(("192.168.1.101", 8000))  
s2.send(json.dumps({
	"type": "token",
	"data": "123"
}).encode('utf-8'))
try:
	while True:
		szBuf = s2.recv(256)
		szObj = json.loads(szBuf.decode('utf-8'))
		if szObj["type"] == "RTS":
			s2.send(json.dumps({
				"type": "CTS"
			}).encode('utf-8'))
except:
	s2.close()
