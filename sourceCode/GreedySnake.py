# -*- coding: utf-8
from random import randint
import time

from machine import Pin
import screen


########################### Program  Bugs ###########################

# BUG_1: 蛇身长度小于3时也可能吃到减二食物，最终蛇长变为1
# 出现场景：蛇长超过10后，遇见减二白块，先撞死自己，蛇身变为3，再吃白块
# 修复方法：每次游戏结束后都在蛇身初始化后重新生成食物

# BUG_2: 蛇从左向右穿过右墙时，和墙间隔1格时即穿墙
# 出现场景：蛇从左向右穿过右墙时
# 修复方法：这是由于self.grid.width实际是能取到的，修改向右移动逻辑：
#           new = ((head[0] + 1) % (self.grid.width + 1), head[1])

# BUG_3: 长按与蛇前进方向相同的方向键，可以达到二倍速
# 出现场景：长按与蛇前进方向相同的方向键，在key_release函数中多调用了1次move()
# 修复方法：虽然这不是bug，但想修复，可以在key_release屏蔽按键时屏蔽掉同方向

# BUG_4: 无论如何按键蛇都不能贴着身体掉头，两次转向间隔了一个方块
# 出现场景：连按两次同方向转向键，蛇头与蛇身隔了一行
# 修复方法：产生原因同BUG_3中描述的问题：按键会触发一次move。去除key_release中的move，
#           为了保留二倍速效果，判断按键同方向时，调用move()

# BUG_5: 游戏并不能暂停
# 修复方法： 按键太少了，那就把暂停功能去了呀，提高性能

# BUG_6: KeyInterupt后重新下载会崩溃，
# 猜想这是因为键盘中断导致了现场没有恢复到原始状态
# 在没有操作系统手册的前提下，无解
# 后来发现程序运行久了也会崩，可能垃圾回收机制有问题
########################### Inner Methods ###########################

# 清屏
# screen.clear();

# 屏幕画线
# screen.drawline(start_x, start_y, end_x, end_y, line_weight, color)

########################### Inner  Params ###########################

SCREEN_WIDTH = 239   # px 从0开始
SCREEN_HEIGHT = 320  # px 从0开始
KEY_DOWN  = 36  # 右键引脚号
KEY_LEFT  = 39  # 下键引脚号
KEY_UP    = 34  # 左键引脚号
KEY_RIGHT = 35  # 上键引脚号
PINS = [KEY_RIGHT, KEY_DOWN, KEY_LEFT, KEY_UP]

########################### Program start ###########################

keys = [Pin(p, Pin.IN) for p in PINS]  # 初始化引脚对象列表

class Grid(object): # 格栅系统
	def __init__(self, master = None, x = 10, y = 10, w = 222, h = 303, s = 10):
		self.x = x  # 格栅系统左上角横坐标：px
		self.y = y  # 格栅系统左上角纵坐标：px
		self.w = w  # 格栅系统宽度：px
		self.h = h  # 格栅系统高度：px
		self.s = s  # 格子的边长：px
		self.width  = w//self.s - 1  # 宽度：格子
		self.height = h//self.s - 1  # 高度：格子
		self.bg = 0x000000           # 背景色：16进制RGB
		# print(self.width, self.height)  # 输出控制台提示信息
		
		#画背景
		for i in range(SCREEN_HEIGHT):  # 用贯穿上下的竖线铺满屏幕
			screen.drawline(0, i, SCREEN_WIDTH, i, 1, self.bg);
		
		#画边界
		screen.drawline(x,			y,		x + w - 1,	y,		1,	0xFFFFFF);  # 上边框
		screen.drawline(x + w - 1,	y,		x + w - 1,	y + h,	1,	0xFFFFFF);  # 右边框
		screen.drawline(x,			y + h,	x + w - 1,	y + h,	1,	0xFFFFFF);  # 下边框
		screen.drawline(x,			y,		x,			y + h,	1,	0xFFFFFF);  # 左边框

	def draw(self, pos, color):
		# pos 是一个元组(横坐标：格子，纵坐标：格子)
		x = pos[0] * self.s + self.x + 1  # 格子坐标转绝对坐标：px
		y = pos[1] * self.s + self.y + 1  # 格子坐标转绝对坐标：px
		for i in range(self.s):  # 用贯穿上下的竖线铺满一格
			screen.drawline(x, y + i, x + self.s - 1, y + i, 1, color);
	
class Food(object):  # 食物类
	def __init__(self, grid, color = 0xFF0000):
		self.grid = grid    # 格栅系统
		self.color = color  # 食物颜色
		self.set_pos()      # 设置食物坐标
		self.type = 1       # 食物类型

	def set_pos(self):
		x = randint(0, self.grid.width - 1)   # 随机横坐标
		y = randint(0, self.grid.height - 1)  # 随机纵坐标
		self.pos = (x, y)  # 设置食物坐标

	def display(self):  # 在屏幕上绘制食物
		self.grid.draw(self.pos, self.color)

class Snake(object):  # 蛇类
	def __init__(self, grid, color = 0xFFFFFF):
		self.grid = grid    # 格栅系统
		self.color = color  # 蛇的颜色
		self.body = [(5, 5), (5, 6), (5, 7)]  # 初始化身段位置
		self.direction = KEY_UP  # 初始化方向向上
		for i in self.body:  # 在屏幕上绘制蛇
			self.grid.draw(i, self.color)

	# 这个方法用于游戏重新开始时初始化贪吃蛇的位置
	def initial(self):
		while not len(self.body) == 0:  # 清空蛇身并用背景擦除
			pop = self.body.pop()
			self.grid.draw(pop, self.grid.bg)
		self.body = [(8, 11), (8, 12), (8, 13)]  # 重新初始化身段位置
		self.direction = KEY_UP  # 重新初始化方向向上
		self.color = 0xFFFFFF  # 初始化蛇的颜色
		for i in self.body:  # 在屏幕上绘制蛇
			self.grid.draw(i, self.color)

	# 蛇像一个指定点移动
	def move(self, new):
		self.body.insert(0, new)  # 队列头插入新点
		pop = self.body.pop()     # 队列尾去除旧点
		self.grid.draw(pop, self.grid.bg)  # 绘制头部新点
		self.grid.draw(new, self.color)    # 擦除尾部旧点

	# 蛇像一个指定点移动，并增加长度
	def add(self, new):
		self.body.insert(0, new)           # 队列头插入新点
		self.grid.draw(new, self.color)    # 绘制头部新点

	# 蛇吃到了特殊食物1，剪短自身的长度
	def cut_down(self, new):
		self.body.insert(0, new)           # 队列头插入新点
		self.grid.draw(new, self.color)    # 绘制头部新点
		for i in range(3):                 # 从尾部擦除3个点
			pop = self.body.pop()
			self.grid.draw(pop, self.grid.bg)

	# 蛇吃到了特殊食物2，回到最初长度
	def init(self, new):
		self.body.insert(0, new)           # 队列头插入新点
		self.grid.draw(new, self.color)    # 绘制头部新点
		while len(self.body) > 3:          # 从尾部擦除，直到只剩3个点
			pop = self.body.pop()
			self.grid.draw(pop, self.grid.bg)

	 # 蛇吃到了特殊食物3，改变了自身的颜色,纯属好玩
	def change(self, new, color):
		self.color = color        # 修改自身颜色
		self.body.insert(0, new)  # 队列头插入新点
		for item in self.body:    # 用新颜色覆盖所有点
			self.grid.draw(item, self.color)
class SnakeGame():  # 贪吃蛇游戏控制
	def __init__(self):
		screen.clear();  # 清屏
		self.grid = Grid()  # 初始化格栅系统
		self.snake = Snake(self.grid)  # 初始化蛇
		self.food = Food(self.grid)  # 初始化食物
		self.gameover = False  # 游戏结束标志位
		self.score = 0  # 分数
		self.speed = 125  # 时间间隔，反比于速度
		self.display_food()  # 展示一个食物

	# type1:普通食物  type2:减少2  type3:大乐透，回到最初状态  type4:吃了会变色
	def display_food(self):
		self.food.color = 0xFF0000  # 默认食物颜色
		self.food.type = 1          # 默认食物类型
		rand = randint(0, 39)       # 产生随机数
		if rand == 39:    # 大乐透概率：1/40
			self.food.color = 0x00FF00
			self.food.type = 3
		elif rand <= 4:  # 变色食物概率：5/40
			self.food.color = 0x0000FF
			self.food.type = 4
		elif len(self.snake.body) > 10 and rand <= 14:  # 超长后减少2食物概率：10/40
			self.food.color = 0xFFFFFF
			self.food.type = 2
		
		# 不超长普通食物概率：34/40，超长后普通食物概率：24/40
		
		while (self.food.pos in self.snake.body):
			self.food.set_pos()  # 在蛇身外面随机位置
		self.food.display()
		# print(self.food.type)

	# 这个方法用于游戏重新开始时初始化游戏
	def initial(self):
		self.gameover = False
		self.score = 0
		self.grid.draw(self.food.pos, self.grid.bg) # 用于解决BUG_1
		self.snake.initial()
		self.display_food()                         # 用于解决BUG_1
	
	# 运行游戏
	def run(self):
		while True:
			for i in range(len(keys)):  # 这里原来写的太罗嗦，效率也低
				if keys[i].value() == 0:  # 如果有键按下：低电平
					self.key_release(i)
			if self.gameover == True:  # 如果游戏结束则重新开始
				self.initial()
			else:
				self.move()
			time.sleep_ms(self.speed)  # 延时

	def move(self, color = 0xFFFFFF):
		# 计算蛇下一次移动的点
		head = self.snake.body[0]
		if self.snake.direction == KEY_UP:
			if head[1] - 1 < 0:  # 头部将要超出上边界则进入下边界
				new = (head[0], self.grid.height)
			else:                # 否则头部上移一格
				new = (head[0], head[1] - 1)
		elif self.snake.direction == KEY_DOWN:  # 头部下移一格，超出下边界则从上边界开始
			new = (head[0], (head[1] + 1) % self.grid.height)
		elif self.snake.direction == KEY_LEFT:
			if head[0] - 1 < 0:  # 头部将要超出左边界则进入右边界
				new = (self.grid.width, head[1])
			else:                # 否则头部左移一格
				new = (head[0] - 1, head[1])
		else:
			new = ((head[0] + 1) % (self.grid.width + 1), head[1])  # 修复BUG_2
			# 撞到自己，设置游戏结束的标志位，等待下一循环
		if new in self.snake.body:
			self.gameover = True
		# 吃到食物：根据食物类型调用对应的方法
		elif new == self.food.pos:
			# print(self.food.type)
			if self.food.type == 1:
				self.snake.add(new)
			elif self.food.type == 2:
				self.snake.cut_down(new)
			elif self.food.type == 4:
				self.snake.change(new, 0x0000FF)
			elif self.food.type == 3:
				self.snake.init(new)
			self.display_food()  # 更新一个新食物
			
		#什么都没撞到，继续前进
		else:
			self.snake.move(new)
	def key_release(self, key):
		keymatch = PINS  # 用设置中的引脚列表提高泛化能力
		key_dict = {     # 使用整型数字典提高存储和查询性能
			KEY_UP: KEY_DOWN, 
			KEY_DOWN: KEY_UP,
			KEY_LEFT: KEY_RIGHT,
			KEY_RIGHT: KEY_LEFT
		}
		# print(keymatch[key])
		# 蛇不可以向自己的反方向走
		if keymatch[key] in key_dict.keys():
			if keymatch[key] == self.snake.direction:  # 如果按键与当前前进方向一致
				self.move()  # 多走一步，产生二倍速的效果
			elif not keymatch[key] == key_dict[self.snake.direction]:
				self.snake.direction = keymatch[key]  # 改变当前方向
		
if __name__ == '__main__':
	snake = SnakeGame()
	snake.run()
