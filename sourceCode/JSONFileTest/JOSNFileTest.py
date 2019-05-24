import ujson

class CFG():

	def __init__(self, path):
		self.cfg = None
		with open(path, "rb") as cfgFile: # ujson.loads()将字符串加载为python字典
			self.cfg = ujson.loads(cfgFile.read().decode("utf-8"))
	def __call__(self, argument):  # 对象可以作为函数调用，给出参数名，返回参数值
		assert argument in self.cfg, "wrong argument name"
		return self.cfg[argument]

if __name__ == '__main__':
	cfg = CFG("params.json")
	print("From JSON File: SERVER_IP =", cfg("SERVER_IP"))
	print("From JSON File: SERVER_PORT =", cfg("SERVER_PORT"))