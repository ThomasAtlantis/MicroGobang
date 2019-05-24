import text as _text
import screen as _screen
import network, usocket, ujson
from machine import Pin, TouchPad
import time, sys

class Key():  # 按键抽象类

	def __init__(self, pinNum, pinMode, name):
		self.pin = Pin(pinNum, pinMode)
		self.name = name
		self.pressed = False

	def keyDown(self):
		pass

class TouchKey(Key):  # 触摸键

	def __init__(self, pinNum, pinMode, name):
		super(TouchKey, self).__init__(pinNum, pinMode, name)
		self.touchPad = TouchPad(self.pin)

	def keyDown(self):
		threshold = 550  # 触摸键read()值按下和未按下的分界
		if self.touchPad.read() > threshold:
			self.pressed = False
		elif not self.pressed:  # 控制边沿检测
			time.sleep(0.02)
			if self.touchPad.read() <= threshold:
				self.pressed = True
				return True
		return False

class PressKey(Key):  # 按动键

	def keyDown(self):
		if self.pin.value() == 1:
			self.pressed = False
		elif not self.pressed:  # self.pin.value() == 0为按下状态
			self.pressed = True
			return True
		return False

class CFG():  # 从JSON文件读取配置信息类

	def __init__(self, path):
		self.cfg = None
		with open(path, "rb") as cfgFile:  # 读取文件并解析为python字典
			self.cfg = ujson.loads(cfgFile.read().decode("utf-8"))
	def __call__(self, argument):
		assert argument in self.cfg, "wrong argument name"  # 断言字典中存在指定参数名
		return self.cfg[argument]

class CSS(CFG):  # 从css的JSON文件读取样式表信息类

	def __call__(self, elementID):
		assert elementID in self.cfg, "wrong element ID"
		# 允许x, y在样式表中缺省，默认为0
		# 最终转换为self.cfg[elementID] = {
		#   ...
		# 	"pos": (x, y),
		# 	...
		# }
		# 因为JSON解析不允许嵌套元组，只允许字典
		x = y = 0
		if "y" in self.cfg[elementID]:
			y = self.cfg[elementID]["y"]
			del self.cfg[elementID]["y"]
		if "x" in self.cfg[elementID]:
			x = self.cfg[elementID]["x"]
			del self.cfg[elementID]["x"]
		self.cfg[elementID]["pos"] = (x, y)
		if "bg" in self.cfg[elementID]:  # 将背景色转换为整型
			self.cfg[elementID]["bg"] = int(self.cfg[elementID]["bg"], 16)
		if "fg" in self.cfg[elementID]:  # 将前景色转换为整型
			self.cfg[elementID]["fg"] = int(self.cfg[elementID]["fg"], 16)
		return self.cfg[elementID]

class Label():
	# Max number of characters one line: 15
	# text为标签的文字
	# pos为标签左上角位置
	# fg和bg分别为文字颜色和背景颜色
	# center为true时，标签会自动居中
	def __init__(self, text, pos, fg=0x000000, bg=0xFFFFFF, center=False):
		assert len(text) * 16 + pos[0] <= 241, "Text too long for one line"
		self.text = text
		self.x, self.y = pos[0] - 1, pos[1] - 1
		if center:
			self.x = (240 - len(text) * 16) // 2  # 计算出居中时的x坐标
		self.fg, self.bg = fg, bg
		self.show()

	def setText(self, text):
		self.clear()
		self.text = text
		self.show()

	def clear(self):  # 用背景色清空标签区域的文字
		w, h = len(self.text) * 16, 16
		for i in range(h):
			_screen.drawline(self.x, self.y + i, self.x + w, self.y + i, 1, self.bg)

	def show(self):  # 显示文字
		_text.draw(self.text, self.x, self.y, self.fg, self.bg)

class Canvas():
	
	def __init__(self):
		self.width = 240  # 画布与屏幕等宽
		self.height = 320  # 画布与屏幕等高

	def clear(self):
		_screen.clear()  # 清屏

	# 功能：绘制线段
	# pos1，pos2分别为线段两个端点，用元组表示(x, y)
	# color为线段颜色，整型数
	# weight为线宽，整数
	def drawLine(self, pos1, pos2, color=0x000000, weight=1):
		assert self.width >= pos1[0] >= 1 and self.width >= pos2[0] >= 1, "X out of border"
		assert self.height >= pos1[1] >= 1 and self.height >= pos2[1] >= 1, "Y out of border"
		x1, y1 = pos1[0] - 1, pos1[1] - 1
		x2, y2 = pos2[0] - 1, pos2[1] - 1
		_screen.drawline(x1, y1, x2, y2, weight, color)
	
	# 功能：绘制空心矩形
	# pos1，pos2分别为矩形左上角和右下角两个端点，用元组表示(x, y)
	# color为线条颜色，整型数
	# weight为线宽，整数
	def drawRect(self, pos1, pos2, color=0x000000, weight=1):
		assert self.width >= pos1[0] >= 1 and self.width >= pos2[0] >= 1, "X out of border"
		assert self.height >= pos1[1] >= 1 and self.height >= pos2[1] >= 1, "Y out of border"
		half_weight = weight // 2
		x1, y1 = pos1[0] - 1, pos1[1] - 1
		x2, y2 = pos2[0] - 1, pos2[1] - 1
		_screen.drawline(x1 - half_weight, y1, x2 + half_weight, y1, weight, color)
		_screen.drawline(x1 - half_weight, y2, x2 + half_weight, y2, weight, color)
		_screen.drawline(x1, y1, x1, y2, weight, color)
		_screen.drawline(x2, y1, x2, y2, weight, color)

	# 功能：绘制实心矩形
	# pos1，pos2分别为矩形左上角和右下角两个端点，用元组表示(x, y)
	# borderColor为边框颜色，整型数
	# contentColor为填充颜色，整型数
	def filledRect(self, pos1, pos2, borderColor=0x000000, contentColor=0xFFFFFF):
		x1, y1 = pos1[0] - 1, pos1[1] - 1
		x2, y2 = pos2[0] - 1, pos2[1] - 1
		_screen.drawline(x1, y1, x2, y1, 1, borderColor)
		_screen.drawline(x1, y2, x2, y2, 1, borderColor)
		_screen.drawline(x1, y1, x1, y2, 1, borderColor)
		_screen.drawline(x2, y1, x2, y2, 1, borderColor)
		for i in range(y1 + 1, y2):
			_screen.drawline(x1 + 1, i, x2 - 1, i, 1, contentColor)

	# 功能：绘制矩形定位光标（边线断开的空心矩形）
	# pos1，pos2分别为矩形左上角和右下角两个端点，用元组表示(x, y)
	# color为线条颜色，整型数
	# weight为线宽，整数
	def brokenRect(self, pos1, pos2, size, color=0x000000, weight=1):
		self.drawLine(pos1, (pos1[0] + size, pos1[1]), color, weight)
		self.drawLine((pos2[0] - size, pos1[1]), (pos2[0], pos1[1]), color, weight)
		self.drawLine((pos1[0], pos2[1]), (pos1[0] + size, pos2[1]), color, weight)
		self.drawLine((pos2[0] - size, pos2[1]), pos2, color, weight)
		self.drawLine(pos1, (pos1[0], pos1[1] + size), color, weight)
		self.drawLine((pos1[0], pos2[1] - size), (pos1[0], pos2[1]), color, weight)
		self.drawLine((pos2[0], pos1[1]), (pos2[0], pos1[1] + size), color, weight)
		self.drawLine((pos2[0], pos2[1] - size), pos2, color, weight)

class ChessboardUnit():

	def __init__(self, canvas, pos, side):
		self.canvas = canvas
		self.pos = pos
		self.side = side
		self.empty = True  # 该交叉点是否有落子

	# 落子，role为角色，0代表白棋，1代表黑棋
	def place(self, role):
		if not self.empty:
			return False
		colors = [0xFFFFFF, 0x000000]  # 为不同角色设置棋子颜色
		self.canvas.filledRect(
			(self.pos[0] - self.side + 3, self.pos[1] - self.side + 3), 
			(self.pos[0] + self.side - 3, self.pos[1] + self.side - 3),
			contentColor=colors[role])  # 绘制棋子
		self.empty = False
		return True

	# 交叉点获得焦点
	def focus(self):
		self.canvas.brokenRect(
			(self.pos[0] - self.side, self.pos[1] - self.side), 
			(self.pos[0] + self.side, self.pos[1] + self.side),
			size=5, color=0xFF0000)  # 绘制矩形定位光标

	def blur(self):
		self.canvas.brokenRect(
			(self.pos[0] - self.side, self.pos[1] - self.side), 
			(self.pos[0] + self.side, self.pos[1] + self.side),
			size=5, color=0xFFFFFF)  # 使用背景色擦除矩形定位光标

class Chessboard():

	def __init__(self, canvas, sideUnitNum):
		self.canvas = canvas  # 画布工具
		self.sideUnitNum = sideUnitNum  # 每边的交叉点数
		self.unitSide = canvas.width // sideUnitNum  # 每一小格的边长（像素）
		self.fgColor = 0x3B200B  # 前景色
		self.totalLength = self.unitSide * (self.sideUnitNum - 1)  # 棋盘总边长
		self.startPadding = (self.canvas.width - self.totalLength) // 2  # 棋盘外边距
		self.map = [  # 棋盘数组，每个元素是一个ChessboardUnit
			[
				ChessboardUnit(self.canvas, (self.startPadding + i * self.unitSide, self.startPadding + j * self.unitSide), 
					self.unitSide // 2) for i in range(self.sideUnitNum)
			] for j in range(self.sideUnitNum)
		]
		self.curPos = [sideUnitNum // 2, sideUnitNum // 2]  # 当前光标位置
		self.map[self.curPos[1]][self.curPos[0]].focus()  # 初始光标位置为中心点

	# 绘制棋盘
	def draw(self):
		self.canvas.drawRect((1, 1), (self.canvas.width, self.canvas.width), self.fgColor, 3)  # 绘制边框
		for i in range(self.sideUnitNum):  # 绘制内部交叉线
			self.canvas.drawLine(
				(self.startPadding + i * self.unitSide, self.startPadding), 
				(self.startPadding + i * self.unitSide, self.startPadding + self.totalLength),
				self.fgColor)
			self.canvas.drawLine(
				(self.startPadding, self.startPadding + i * self.unitSide),
				(self.startPadding + self.totalLength, self.startPadding + i * self.unitSide),
				self.fgColor)

	# 向direction指定的方向移动当前光标一格
	def move(self, direction):
		self.map[self.curPos[1]][self.curPos[0]].blur()
		if direction == "RIGHT":
			self.curPos[0] = (self.curPos[0] + 1) % self.sideUnitNum
		elif direction == "LEFT":
			self.curPos[0] = (self.curPos[0] + self.sideUnitNum - 1) % self.sideUnitNum
		elif direction == "DOWN":
			self.curPos[1] = (self.curPos[1] + 1) % self.sideUnitNum
		elif direction == "UP":
			self.curPos[1] = (self.curPos[1] + self.sideUnitNum - 1) % self.sideUnitNum
		self.map[self.curPos[1]][self.curPos[0]].focus()

	# 移动当前光标到指定位置
	def goto(self, pos):
		self.map[self.curPos[1]][self.curPos[0]].blur()
		self.curPos[0] = pos[0]
		self.curPos[1] = pos[1]
		self.map[self.curPos[1]][self.curPos[0]].focus()

	# 角色落子
	def place(self, role):
		if self.map[self.curPos[1]][self.curPos[0]].place(role):
			return self.curPos
		else:
			return []

class MicroGobangClient():

	def __init__(self):
		self.keys = [  # 可用按键表
			PressKey(36, Pin.IN, "DOWN"),
			PressKey(39, Pin.IN, "LEFT"),
			PressKey(34, Pin.IN, "UP"),
			PressKey(35, Pin.IN, "RIGHT"),
			TouchKey(27, Pin.IN, "SW5"),
			TouchKey(33, Pin.IN, "SW4"),
			TouchKey(32, Pin.IN, "SW3"),
			TouchKey( 4, Pin.IN, "SW2")
		]
		self.keysNote = {  # 按键说明信息
			"RIGHT": "右", 
			"LEFT" : "左", 
			"UP"   : "上", 
			"DOWN" : "下"
		}

		self.canvas = Canvas()  # 画布绘图工具
		self.css = CSS("css.json")  # 加载CSS样式表
	
		self.welcomePage()  # 显示欢迎页，因为WiFi配置需要一定时间

		self.wlan = self.sender = None
		self.cfg = CFG("cfg.json")  # 加载网络配置信息
		try:
			self.connectWifi(self.cfg("SSID"), self.cfg("PASSWORD"))  # 连接WiFi
			print("connected to <wifi://{}>".format(self.cfg("SSID")))
			self.sender = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
			self.sender.connect((self.cfg("SERVER_IP"), self.cfg("SERVER_PORT")))  # 与服务器建立socket连接
			print("connected to <sock://{}:{}>".format(self.cfg("SERVER_IP"), self.cfg("SERVER_PORT")))
		except Exception as err:
			print(err)
			if (self.sender):
				self.sender.close()
			self.wlan.disconnect()
			self.wlan.active(False)
			sys.exit()

	# 连接WiFi的功能函数
	def connectWifi(self, ssid, passwd):
		network.WLAN(network.AP_IF).active(True)
		self.wlan=network.WLAN(network.STA_IF)
		self.wlan.active(True)
		self.wlan.disconnect()
		self.wlan.connect(ssid,passwd)
		while(self.wlan.ifconfig()[0]=='0.0.0.0'):
			time.sleep(1)
		return True
	
	# 将json字典转换为字节流
	def msg(self, json):
		return ujson.dumps(json).encode("utf-8")

	# 暂停，按任意键继续
	def pause(self):
		loopFlag = True
		while loopFlag:
			for key in self.keys:
				if key.keyDown():
					loopFlag = False
					break

	# 欢迎页面
	def welcomePage(self):
		self.canvas.clear()
		# **是解析字典的意思
		# func(**{"x": 0, "y": 0})相当于func(x=0, y=0)
		Label("Micro Gobang", 			**self.css("gameName"))
		Label("Made By", 				**self.css("author_1"))
		Label("东北大学物联网工程", 	**self.css("author_2"))
		Label("1601 刘尚育", 			**self.css("author_3"))
		Label("liushangyu.xyz", 		**self.css("author_w"))

	# 介绍页面
	def introductionPage(self):
		self.canvas.clear()
		Label("口令输入界面键位说明", 	**self.css("ins_1"))
		Label("方向键 -- 输入口令", 	**self.css("ins_2"))
		Label("SW2 -- 清空输入", 		**self.css("ins_3"))
		Label("SW5 -- 匹配对手", 		**self.css("ins_4"))
		Label("SW3 -- 退出游戏", 		**self.css("ins_5"))
		Label("对局室界面键位说明", 	**self.css("ins_6"))
		Label("方向键 -- 移动光标", 	**self.css("ins_7"))
		Label("SW5 -- 确认落子", 		**self.css("ins_8"))
		Label("按任意键继续", 			**self.css("ins_9"))
		self.pause()

	def inputTokenPage(self):
		self.canvas.clear()
		tokenLen = 6  # 口令长度
		Label("Input Token", **self.css("inputTip"))  # 输入提示信息
		inputLabelWidth = (self.canvas.width - 10) // tokenLen
		inputLabels = [Label(" ", (16 + inputLabelWidth * i, 121)) for i in range(tokenLen)]  # 显示口令内容的标签
		for i in range(tokenLen):  # 口令内容下的小短线
			self.canvas.drawLine((16 + i * inputLabelWidth, 142), (32 + i * inputLabelWidth, 142), weight=3)
		
		curTokenIndex = 0
		token = ""
		loopFlag = True
		while loopFlag:
			for key in self.keys:
				if key.keyDown():  # 如果有键按下
					if isinstance(key, PressKey) and curTokenIndex < tokenLen:  # 如果是按动键且当前输入位置没有超出口令总长
						inputLabels[curTokenIndex].setText(self.keysNote[key.name])  # 更新当前位口令文字
						token += self.keysNote[key.name]  # 记录口令内容
						curTokenIndex += 1  # 当前口令位置右移
					elif isinstance(key, TouchKey):
						if key.name == "SW2":  # 清空输入
							for label in inputLabels:
								label.setText(" ")
							token = ""
							curTokenIndex = 0
						elif key.name == "SW3":  # 退出游戏
							self.sender.send(self.msg({
								"type": "offline"
							}))
							self.sender.close()
							self.wlan.disconnect()
							self.wlan.active(False)
							self.canvas.clear()
							Label("Game Over", **self.css("gameOver"))
							sys.exit()
						elif key.name == "SW5" and curTokenIndex == tokenLen:  # 匹配对手
							self.sender.send(self.msg({
								"type": "token",
								"data": token
							}))
							
							# 提示信息
							Label("seeking rival", (0, 174), center=True)
							waitAnimation = Label(" " * 6, (0, 210), center=True)
							for i in range(6):
								waitAnimation.setText("." * (i + 1))
								time.sleep(0.2)

							while True:
								szBuf = self.sender.recv(256)  # 阻塞，等待服务器发来匹配结果
								if szBuf:
									szObj = ujson.loads(szBuf.decode("utf-8"))
									if szObj["type"] == "startGame":  # 消息类型为开始游戏
										self.role = szObj["data"]  # 获得游戏角色
										break
							loopFlag = False
							break

	# 对局室页面
	def gameRoomPage(self):
		
		self.canvas.clear()
		chessboard = Chessboard(self.canvas, 13)  # 生成13x13的棋盘
		chessboard.draw()  # 绘制棋盘

		tipLabel = Label(" " * 12, (0, self.canvas.width + 20), center=True)  # 提示信息
		selfRole = 1 if self.role == "black" else 0  # 己方角色
		rivalRole = 1 - selfRole  # 对方角色

		curRole = 1
		gameOver = False
		while not gameOver:
			if curRole == selfRole:  # 如果当前回合为己方回合
				tipLabel.setText(" your  turn ")
				scanning = True
				while scanning:
					for key in self.keys:
						if key.keyDown():  # 如果有键按下
							if isinstance(key, PressKey):  # 如果按键是按动键
								chessboard.move(key.name)  # 移动光标
							elif key.name == "SW2":  # 投降
								self.sender.send(self.msg({
									"type": "surrender"
								}))
								tipLabel.setText(" surrender! ")
								scanning = False
								gameOver = True
								break
							elif key.name == "SW5":  # 落子
								pos = chessboard.place(selfRole)
								if pos:
									self.sender.send(self.msg({
										"type": "place",
										"data": {
											"x": pos[0],
											"y": pos[1]
										}
									}))
									scanning = False
									break

			else:  # 当前为对方回合
				tipLabel.setText("rival's turn")
				while True:
					szBuf = self.sender.recv(256)  # 阻塞，等待服务器发来消息
					if szBuf:
						szObj = ujson.loads(szBuf.decode("utf-8"))
						if szObj["type"] == "place":  # 同步落子
							pos = szObj["data"]["x"], szObj["data"]["y"]
							chessboard.goto(pos)  # 移动当前光标
							chessboard.place(rivalRole)  # 绘制落子
							break
						elif szObj["type"] == "win":  # 胜利
							tipLabel.setText("  you  win  ")
							gameOver = True
							break
						elif szObj["type"] == "lose":  # 失败
							pos = szObj["data"]["x"], szObj["data"]["y"]
							chessboard.goto(pos)  # 失败也要同步最后一步落子
							chessboard.place(rivalRole)
							tipLabel.setText("  you lose  ")
							gameOver = True
							break
			curRole = 1 - curRole  # 交换棋权
		time.sleep(3)  # 维持一段时间给玩家审视棋局，然后结束

	def run(self):
		self.introductionPage()
		while True:  # 在输入口令页面和对居室页面循环
			self.inputTokenPage()
			self.gameRoomPage()

if __name__ == '__main__':
	MicroGobangClient().run()