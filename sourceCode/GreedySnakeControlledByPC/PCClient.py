import socket
import time
import pygame  # python的第三方游戏库，这里用来监听键盘事件
import sys

def main():
	pygame.init()  # 初始化必须有
	pygame.display.set_caption("Hello world")  # 窗口标题栏文字
	screen = pygame.display.set_mode((640,480), 0, 32)  # 窗口大小和左上角位置
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(('192.168.43.196', 10000))  # 连接Skids上的服务器
	while True:
		for event in pygame.event.get():  # 有事件发生
			if event.type == pygame.QUIT:  # 如果是关闭事件
				sys.exit()
			if event.type == pygame.KEYDOWN:  # 如果是按键按下
				if event.key == pygame.K_LEFT:  # 如果是方向键左键
					client.send("L".encode('utf-8'))  # 发送字符"L"给Skids
					print("L")
				elif event.key == pygame.K_RIGHT:
					client.send("R".encode('utf-8'))
					print("R")
				elif event.key == pygame.K_UP:
					client.send("U".encode('utf-8'))
					print("U")
				elif event.key == pygame.K_DOWN:
					client.send("D".encode('utf-8'))
					print("D")
		client.send("N".encode('utf-8'))  # 发送"N"字符来驱动Skids的蛇移动，否则Skids端等待消息会阻塞
		time.sleep(0.06)  # 可以控制蛇的移动速度

if __name__ == '__main__':
	main()
