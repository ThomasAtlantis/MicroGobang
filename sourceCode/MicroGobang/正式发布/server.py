import threading
import socket
import json
import sys
import random

clientList = []  # 客户端连接池
tokenList = {}   # 口令字典
clientListMutex = threading.Lock()  # 访问客户端连接池的锁
tokenListMutex = threading.Lock()   # 访问口令字典的锁

class Client(threading.Thread):  # 客户端线程

    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        while True:  # 这里一定要用循环，避免接收到其他消息产生干扰
            szBuf = self.conn.recv(1024)  # 接收客户端发来的消息
            szObj = json.loads(szBuf.decode('utf-8'))  # 解析为python字典
            if szObj["type"] == "token":  # 如果消息类型为token
                token = szObj["data"]
                print("receive token from %s: %s" % (self.addr, token))
                if tokenListMutex.acquire():  # 获得锁
                    if token in tokenList:
                        tokenList[token].append(self)  # 将客户端加入口令字典中对应口令的客户端列表
                    else:
                        tokenList[token] = [self]
                    tokenListMutex.release()  # 释放锁
                    break
            elif szObj["type"] == "offline":  # 如果消息类型为offline
                print(self.addr, "offline")
                clientList.remove(self)  # 从客户端连接池中删除自己
                break


class ClientMonitor(threading.Thread):  # 客户端监控器

    def run(self):
        while True:
            deleteKeys = []
            if tokenListMutex.acquire():
                for token, clients in tokenList.items():
                    if not clients:  # 如果客户端列表为空
                        deleteKeys.append(token) # 将该token键加入待删除列表
                    elif len(clients) >= 2:
                        newGame = Game(clients[-2:])  # 这里取最后两个客户端
                        newGame.start()  # 游戏房间线程开始
                        clients.pop()  # 从列表中删除对应的玩家
                        clients.pop()
                if deleteKeys: 
                    for deleteKey in deleteKeys:
                        del tokenList[deleteKey]  # 删除待删除列表中指定的key
                tokenListMutex.release()

class Game(threading.Thread):  # 游戏房间线程

    def __init__(self, players):
        threading.Thread.__init__(self)
        random.shuffle(players)  # 随机角色分配
        self.players = players
        self.map = [[2 for i in range(13)] for j in range(13)]  # 棋盘大小为13x13
        self.gameOver = False

    def startGame(self):
        roles = ["black", "white"]
        for i in range(2):  # 分配角色并通知客户端
            self.players[i].conn.send(json.dumps({
                "type": "startGame",
                "data": roles[i]
            }).encode("utf-8"))
        
        BLACK, WHITE = 0, 1
        curTurn = BLACK  # 当前回合
        while not self.gameOver:
            while True:
                szBuf = self.players[curTurn].conn.recv(1024)  # 接收当前回合玩家消息
                szObj = json.loads(szBuf.decode('utf-8'))  # 解析为python字典
                if szObj["type"] == "surrender":  # 如果消息类型为投降
                    self.gameOver = True
                    self.players[1 - curTurn].conn.send(json.dumps({  # 通知另一方胜利
                        "type": "win"
                    }).encode("utf-8"))
                    break
                elif szObj["type"] == "place":  # 如果消息类型为落子
                    x = szObj["data"]["x"]
                    y = szObj["data"]["y"]
                    self.map[y][x] = curTurn  # 获取落子坐标并在棋盘数组中标记
                    print("black", x, y)
                    if self.checkWinner(x, y, curTurn):  # 如果当前玩家胜利
                        self.players[curTurn].conn.send(json.dumps({  # 通知玩家胜利
                            "type": "win"
                        }).encode("utf-8"))
                        self.players[1 - curTurn].conn.send(json.dumps({  # 通知另一方玩家失败，并更新落子
                            "type": "lose",
                            "data": {
                                "x": szObj["data"]["x"],
                                "y": szObj["data"]["y"]
                            }
                        }).encode("utf-8"))
                        self.gameOver = True
                    else:
                        self.players[1 - curTurn].conn.send(szBuf)  # 另一方玩家同步落子信息
                    curTurn = 1 - curTurn  # 交换棋权
                    break

    def checkWinner(self, curX, curY, role):  # 检测输赢
        # 检测横向是否连成5子
        i = j = 1
        while curX >= i and self.map[curY][curX - i] == role: i += 1
        while curX + j < len(self.map) and self.map[curY][curX + j] == role: j += 1
        if j + i == 6: return True
        # 检测纵向是否连成5子
        i = j = 1
        while curY >= i and self.map[curY - i][curX] == role: i += 1
        while curY + j < len(self.map) and self.map[curY + j][curX] == role: j += 1
        if j + i == 6: return True
        # 检测左上到右下是否连成5子
        i = j = 1
        while curX >= i and curY >= i and self.map[curY - i][curX - i] == role: i += 1
        while curX + j < len(self.map) and curY + j < len(self.map) and self.map[curY + j][curX + j] == role: j += 1
        if j + i == 6: return True
        # 检测左下到右上是否连成5子
        i = j = 1
        while curX >= i and curY + i < len(self.map) and self.map[curY + i][curX - i] == role: i += 1
        while curX + j < len(self.map) and curY >= j and self.map[curY - j][curX + j] == role: j += 1
        if j + i == 6: return True

        return False

    def run(self):
        self.startGame()
        for player in self.players:  # 从连接池中删除原有线程，克隆新线程，同一线程不能开启两次
            newClient = Client(player.conn, player.addr)
            clientList.remove(player)
            clientList.append(newClient)
            newClient.start()

class MicroGobangServer():
    
    def __init__(self):
        # 服务器端IP地址和端口
        # self.SERVER_SOCKET = ("192.168.43.2",  8000)
        # self.SERVER_SOCKET = ("localhost",     8000)
        # self.SERVER_SOCKET = ("192.168.1.107", 8000)
        self.SERVER_SOCKET = ("192.168.1.101", 8000)
        self.sock = None
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(self.SERVER_SOCKET)  # 绑定服务器socket
            self.sock.settimeout(None)  # 设置超时时间无限大
            self.sock.listen(10)  # 设置最大允许连接数
        except Exception as err:
            print(err)
            if (self.sock):
                self.sock.close()
            sys.exit()

    def run(self):
        try:
            print("listening...")
            clinetMonitor = ClientMonitor()
            clinetMonitor.start()  # 开启客户端监控器线程
            while True:
                conn, addr = self.sock.accept()  # 阻塞，等待客户端连接
                conn.settimeout(None)
                client = Client(conn, addr)
                clientList.append(client)  # 将客户端加入连接池
                print(addr, "Joined")
                client.start()  # 开启客户端线程

        except Exception as err:
            print(err)
            if (self.sock):
                self.sock.close()
            sys.exit()

if __name__ == '__main__':
    MicroGobangServer().run()