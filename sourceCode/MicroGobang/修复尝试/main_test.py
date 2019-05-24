import text as _text
import screen as _screen
import network, usocket, ujson
from machine import Pin, TouchPad
import time, sys

class Key():

	def __init__(self, pinNum, pinMode, name):
		self.pin = Pin(pinNum, pinMode)
		self.name = name
		self.pressed = False

	def keyDown(self):
		pass

class TouchKey(Key):

	def __init__(self, pinNum, pinMode, name):
		super(TouchKey, self).__init__(pinNum, pinMode, name)
		self.touchPad = TouchPad(self.pin)

	def keyDown(self):
		threshold = 550
		if self.touchPad.read() > threshold:
			self.pressed = False
		elif not self.pressed:
			time.sleep(0.02)
			if self.touchPad.read() <= threshold:
				self.pressed = True
				return True
		return False

class PressKey(Key):

	def keyDown(self):
		if self.pin.value() == 1:
			self.pressed = False
		elif not self.pressed:
			self.pressed = True
			return True
		return False

class CFG():

	def __init__(self, path):
		self.cfg = None
		with open(path, "rb") as cfgFile:
			self.cfg = ujson.loads(cfgFile.read().decode("utf-8"))
	def __call__(self, argument):
		assert argument in self.cfg, "wrong argument name"
		return self.cfg[argument]

class CSS(CFG):

	def __call__(self, elementID):
		assert elementID in self.cfg, "wrong element ID"
		x = y = 0
		if "y" in self.cfg[elementID]:
			y = self.cfg[elementID]["y"]
			del self.cfg[elementID]["y"]
		if "x" in self.cfg[elementID]:
			x = self.cfg[elementID]["x"]
			del self.cfg[elementID]["x"]
		self.cfg[elementID]["pos"] = (x, y)
		if "bg" in self.cfg[elementID]:
			self.cfg[elementID]["bg"] = int(self.cfg[elementID]["bg"], 16)
		if "fg" in self.cfg[elementID]:
			self.cfg[elementID]["fg"] = int(self.cfg[elementID]["fg"], 16)
		return self.cfg[elementID]

class Label():
	# Max number of characters one line: 15
	def __init__(self, text, pos, fg=0x000000, bg=0xFFFFFF, center=False):
		assert len(text) * 16 + pos[0] <= 241, "Text too long for one line"
		self.text = text
		self.x, self.y = pos[0] - 1, pos[1] - 1
		if center:
			self.x = (240 - len(text) * 16) // 2
		self.fg, self.bg = fg, bg
		self.show()

	def setText(self, text):
		self.clear()
		self.text = text
		self.show()

	def clear(self):
		w, h = len(self.text) * 16, 16
		for i in range(h):
			_screen.drawline(self.x, self.y + i, self.x + w, self.y + i, 1, self.bg)

	def show(self):
		_text.draw(self.text, self.x, self.y, self.fg, self.bg)

class Canvas():
	
	def __init__(self):
		self.width = 240
		self.height = 320

	def clear(self):
		_screen.clear()

	def drawLine(self, pos1, pos2, color=0x000000, weight=1):
		assert self.width >= pos1[0] >= 1 and self.width >= pos2[0] >= 1, "X out of border"
		assert self.height >= pos1[1] >= 1 and self.height >= pos2[1] >= 1, "Y out of border"
		x1, y1 = pos1[0] - 1, pos1[1] - 1
		x2, y2 = pos2[0] - 1, pos2[1] - 1
		_screen.drawline(x1, y1, x2, y2, weight, color)
	
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

	def filledRect(self, pos1, pos2, borderColor=0x000000, contentColor=0xFFFFFF):
		x1, y1 = pos1[0] - 1, pos1[1] - 1
		x2, y2 = pos2[0] - 1, pos2[1] - 1
		_screen.drawline(x1, y1, x2, y1, 1, borderColor)
		_screen.drawline(x1, y2, x2, y2, 1, borderColor)
		_screen.drawline(x1, y1, x1, y2, 1, borderColor)
		_screen.drawline(x2, y1, x2, y2, 1, borderColor)
		for i in range(y1 + 1, y2):
			_screen.drawline(x1 + 1, i, x2 - 1, i, 1, contentColor)

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
		self.empty = True

	def place(self, role):
		if not self.empty:
			return False
		colors = [0xFFFFFF, 0x000000]
		self.canvas.filledRect(
			(self.pos[0] - self.side + 3, self.pos[1] - self.side + 3), 
			(self.pos[0] + self.side - 3, self.pos[1] + self.side - 3),
			contentColor=colors[role])
		self.empty = False
		return True

	def focus(self):
		self.canvas.brokenRect(
			(self.pos[0] - self.side, self.pos[1] - self.side), 
			(self.pos[0] + self.side, self.pos[1] + self.side),
			size=5, color=0xFF0000)

	def blur(self):
		self.canvas.brokenRect(
			(self.pos[0] - self.side, self.pos[1] - self.side), 
			(self.pos[0] + self.side, self.pos[1] + self.side),
			size=5, color=0xFFFFFF)

class Chessboard():

	def __init__(self, canvas, sideUnitNum):
		self.canvas = canvas
		self.sideUnitNum = sideUnitNum
		self.unitSide = canvas.width // sideUnitNum
		self.fgColor = 0x3B200B
		self.totalLength = self.unitSide * (self.sideUnitNum - 1)
		self.startPadding = (self.canvas.width - self.totalLength) // 2
		self.map = [
			[
				ChessboardUnit(self.canvas, (self.startPadding + i * self.unitSide, self.startPadding + j * self.unitSide), 
					self.unitSide // 2) for i in range(self.sideUnitNum)
			] for j in range(self.sideUnitNum)
		]
		self.curPos = [sideUnitNum // 2, sideUnitNum // 2]
		self.map[self.curPos[1]][self.curPos[0]].focus()

	def draw(self):
		self.canvas.drawRect((1, 1), (self.canvas.width, self.canvas.width), self.fgColor, 3)
		for i in range(self.sideUnitNum):
			self.canvas.drawLine(
				(self.startPadding + i * self.unitSide, self.startPadding), 
				(self.startPadding + i * self.unitSide, self.startPadding + self.totalLength),
				self.fgColor)
			self.canvas.drawLine(
				(self.startPadding, self.startPadding + i * self.unitSide),
				(self.startPadding + self.totalLength, self.startPadding + i * self.unitSide),
				self.fgColor)

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

	def goto(self, pos):
		self.map[self.curPos[1]][self.curPos[0]].blur()
		self.curPos[0] = pos[0]
		self.curPos[1] = pos[1]
		self.map[self.curPos[1]][self.curPos[0]].focus()

	def place(self, role):
		if self.map[self.curPos[1]][self.curPos[0]].place(role):
			return self.curPos
		else:
			return []

class MicroGobangClient():

	def __init__(self):
		self.keys = [
			PressKey(36, Pin.IN, "DOWN"),
			PressKey(39, Pin.IN, "LEFT"),
			PressKey(34, Pin.IN, "UP"),
			PressKey(35, Pin.IN, "RIGHT"),
			TouchKey(27, Pin.IN, "SW5"),
			TouchKey(33, Pin.IN, "SW4"),
			TouchKey(32, Pin.IN, "SW3"),
			TouchKey( 4, Pin.IN, "SW2")
		]
		self.keysNote = {
			"RIGHT": "右", 
			"LEFT" : "左", 
			"UP"   : "上", 
			"DOWN" : "下"
		}

		self.canvas = Canvas()
		self.css = CSS("css.json")
	
		self.welcomePage()

		self.wlan = self.sender = None
		self.cfg = CFG("cfg.json")
		try:
			self.connectWifi(self.cfg("SSID"), self.cfg("PASSWORD"))
			print("connected to <wifi://{}>".format(self.cfg("SSID")))
			self.sender = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
			self.sender.connect((self.cfg("SERVER_IP"), self.cfg("SERVER_PORT")))  
			print("connected to <sock://{}:{}>".format(self.cfg("SERVER_IP"), self.cfg("SERVER_PORT")))
		except Exception as err:
			print(err)
			if (self.sender):
				self.sender.close()
			self.wlan.disconnect()
			self.wlan.active(False)
			sys.exit()

	def connectWifi(self, ssid, passwd):
		network.WLAN(network.AP_IF).active(True)
		self.wlan=network.WLAN(network.STA_IF)
		self.wlan.active(True)
		self.wlan.disconnect()
		self.wlan.connect(ssid,passwd)
		while(self.wlan.ifconfig()[0]=='0.0.0.0'):
			time.sleep(1)
		return True

	def msg(self, json):
		return ujson.dumps(json).encode("utf-8")

	def pause(self):
		loopFlag = True
		while loopFlag:
			for key in self.keys:
				if key.keyDown():
					loopFlag = False
					break

	def welcomePage(self):
		self.canvas.clear()
		Label("Micro Gobang", 			**self.css("gameName"))
		Label("Made By", 				**self.css("author_1"))
		Label("东北大学物联网工程", 	**self.css("author_2"))
		Label("1601 刘尚育", 			**self.css("author_3"))
		Label("liushangyu.xyz", 		**self.css("author_w"))

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
		tokenLen = 6
		Label("Input Token", **self.css("inputTip"))
		inputLabelWidth = (self.canvas.width - 10) // tokenLen
		inputLabels = [Label(" ", (16 + inputLabelWidth * i, 121)) for i in range(tokenLen)]
		for i in range(tokenLen):
			self.canvas.drawLine((16 + i * inputLabelWidth, 142), (32 + i * inputLabelWidth, 142), weight=3)
		
		curTokenIndex = 0
		token = ""
		loopFlag = True
		while loopFlag:
			for key in self.keys:
				if key.keyDown():
					if isinstance(key, PressKey) and curTokenIndex < tokenLen:
						inputLabels[curTokenIndex].setText(self.keysNote[key.name])
						token += self.keysNote[key.name]
						curTokenIndex += 1
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

							Label("seeking rival", (0, 174), center=True)
							waitAnimation = Label(" " * 6, (0, 210), center=True)
							for i in range(6):
								waitAnimation.setText("." * (i + 1))
								time.sleep(0.2)

							while True:
								szBuf = self.sender.recv(256)
								if szBuf:
									szObj = ujson.loads(szBuf.decode("utf-8"))
									if szObj["type"] == "RTS":
										self.sender.send(self.msg({
											"type": "CTS"
										}))
									elif szObj["type"] == "startGame":
										self.role = szObj["data"]
										break
							loopFlag = False
							break

	def gameRoomPage(self):
		
		self.canvas.clear()
		chessboard = Chessboard(self.canvas, 13)
		chessboard.draw()

		tipLabel = Label(" " * 12, (0, self.canvas.width + 20), center=True)
		selfRole = 1 if self.role == "black" else 0
		rivalRole = 1 - selfRole

		curRole = 1
		gameOver = False
		while not gameOver:
			if curRole == selfRole:
				tipLabel.setText(" your  turn ")
				scanning = True
				while scanning:
					for key in self.keys:
						if key.keyDown():
							if isinstance(key, PressKey):
								chessboard.move(key.name)
							elif key.name == "SW2":
								self.sender.send(self.msg({
									"type": "surrender"
								}))
								tipLabel.setText(" surrender! ")
								scanning = False
								gameOver = True
								break
							elif key.name == "SW5":
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

			else:
				tipLabel.setText("rival's turn")
				while True:
					szBuf = self.sender.recv(256)
					if szBuf:
						szObj = ujson.loads(szBuf.decode("utf-8"))
						if szObj["type"] == "place":
							pos = szObj["data"]["x"], szObj["data"]["y"]
							chessboard.goto(pos)
							chessboard.place(rivalRole)
							break
						elif szObj["type"] == "win":
							tipLabel.setText("  you  win  ")
							gameOver = True
							break
						elif szObj["type"] == "lose":
							pos = szObj["data"]["x"], szObj["data"]["y"]
							chessboard.goto(pos)
							chessboard.place(rivalRole)
							tipLabel.setText("  you lose  ")
							gameOver = True
							break
			curRole = 1 - curRole
		time.sleep(3)

	def run(self):
		self.introductionPage()
		while True:
			self.inputTokenPage()
			self.gameRoomPage()

if __name__ == '__main__':
	MicroGobangClient().run()