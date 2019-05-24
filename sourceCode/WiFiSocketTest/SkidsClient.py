from machine import Pin
import network, usocket
import time

KEY_DOWN  = 36  # 右键引脚号
KEY_LEFT  = 39  # 下键引脚号
KEY_UP    = 34  # 左键引脚号
KEY_RIGHT = 35  # 上键引脚号
PINS = [KEY_RIGHT, KEY_DOWN, KEY_LEFT, KEY_UP]
SSID	 = "liuchen"
PASSWORD = "liuchen88"
SERVER_SOCKET = "192.168.1.109", 8000
wlan = sender = None
keys = [Pin(p, Pin.IN) for p in PINS]
keys_note = ["RIGHT", "DOWN", "LEFT", "UP"]
keys_stat = [1, 1, 1, 1]

# 连接WiFi的方法，传入WiFi名和密码
def connectWifi(ssid,passwd):
	global wlan
	network.WLAN(network.AP_IF).active(True)
	wlan=network.WLAN(network.STA_IF)
	wlan.active(True)
	wlan.disconnect()
	wlan.connect(ssid,passwd)
	while(wlan.ifconfig()[0]=='0.0.0.0'):
		time.sleep(1)
	return True

def main():
	try:
		connectWifi(SSID, PASSWORD)
		my_ip = wlan.ifconfig()[0]  # 获取DHCP分配到的自己的IP
		print("wifi connected")
		sender = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
		sender.connect(SERVER_SOCKET)  # 与服务器建立socket连接
		print("socket connected")
		while True:
			for i, key in enumerate(keys):
				if key.value() == 0:
					if keys_stat[i]  == 1:
						sender.send(keys_note[i].encode('utf-8'))  # 发送按键信息给服务器
						keys_stat[i] = 0  # 用来控制边沿检测
				else:
					keys_stat[i] = 1
	except Exception as err:
		print(err)
		if (sender):
			sender.close()
		wlan.disconnect()
		wlan.active(False)

if __name__ == '__main__':
	main()
