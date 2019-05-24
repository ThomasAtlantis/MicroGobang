import threading
import socket
import json
import sys
import random
import time

clientList = []
tokenList = {}
clientListMutex = threading.Lock()
tokenListMutex = threading.Lock()
printMutex = threading.Lock()

class Client(threading.Thread):

    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        try:
            while True:
                szBuf = self.conn.recv(1024)
                szObj = json.loads(szBuf.decode('utf-8')) if szBuf else None
                if szObj and szObj["type"] == "token":
                    token = szObj["data"]
                    if printMutex.acquire():
                        print("receive token from %s: %s" % (self.addr, token))
                        printMutex.release()
                    if tokenListMutex.acquire():
                        if token in tokenList:
                            tokenList[token].append(self)
                        else:
                            tokenList[token] = [self]
                        tokenListMutex.release()
                        break
                elif (szObj and szObj["type"] == "offline") or not szObj:
                    if printMutex.acquire():
                        print(self.addr, "offline")
                        printMutex.release()
                    if clientListMutex.acquire():
                        clientList.remove(self)
                        clientListMutex.release()
                    break
        except (ConnectionResetError, ConnectionAbortedError) as err:
            if printMutex.acquire():
                print(self.addr, "offline")
                printMutex.release()
            if clientListMutex.acquire():
                clientList.remove(self)
                clientListMutex.release()

class ClientMonitor(threading.Thread):

    def run(self):
        while True:
            deleteKeys = []
            if tokenListMutex.acquire():
                for token, clients in tokenList.items():
                    if not clients:
                        deleteKeys.append(token)
                    elif len(clients) >= 2:
                        offlineError = False
                        for player in clients[-2:]:
                            try:
                                if printMutex.acquire():
                                    print("checking", player.addr)
                                    printMutex.release()
                                player.conn.send(json.dumps({
                                    "type": "RTS"
                                }).encode("utf-8"))
                                szBuf = player.conn.recv(256)
                                szObj = json.loads(szBuf.decode('utf-8'))
                                assert szObj["type"] == "CTS"
                            except:
                                if printMutex.acquire():
                                    print(player.addr, "offline lalala")
                                    printMutex.release()
                                if clientListMutex.acquire():
                                    for i in range(len(clientList)):
                                        if clientList[i].addr == player.addr:
                                            clientList.pop(i)
                                            break
                                    clientListMutex.release()
                                clients.remove(player)
                                offlineError = True
                        if not offlineError:
                            newGame = Game(clients[-2:])
                            newGame.start()
                            clients.pop()
                            clients.pop()
                if deleteKeys:
                    for deleteKey in deleteKeys:
                        del tokenList[deleteKey]
                tokenListMutex.release()

class ServerInspector(threading.Thread):

    def run(self):
        while True:
            if printMutex.acquire() and clientListMutex.acquire():
                if clientList:
                    for client in clientList:
                        print(client.addr, end=" ")
                    print()
                clientListMutex.release()
                printMutex.release()
            if printMutex.acquire() and tokenListMutex.acquire():
                if tokenList:
                    for token, clients in tokenList.items():
                        print(token + ":", len(clients), end=" ")
                    print()
                tokenListMutex.release()
                printMutex.release()
            time.sleep(1)

class Game(threading.Thread):

    def __init__(self, players):
        threading.Thread.__init__(self)
        random.shuffle(players)
        self.players = players
        self.map = [[2 for i in range(13)] for j in range(13)]
        self.gameOver = False

    def startGame(self):
        roles = ["black", "white"]
        for i in range(2):
            self.players[i].conn.send(json.dumps({
                "type": "startGame",
                "data": roles[i]
            }).encode("utf-8"))
        
        BLACK, WHITE = 0, 1
        curTurn = BLACK
        try:
            while not self.gameOver:
                while True:
                    szBuf = self.players[curTurn].conn.recv(1024)
                    szObj = json.loads(szBuf.decode('utf-8'))
                    if szObj["type"] == "surrender":
                        self.gameOver = True
                        self.players[1 - curTurn].conn.send(json.dumps({
                            "type": "win"
                        }).encode("utf-8"))
                        break
                    elif szObj["type"] == "place":
                        x = szObj["data"]["x"]
                        y = szObj["data"]["y"]
                        self.map[y][x] = curTurn
                        if printMutex.acquire():
                            print("black", x, y)
                            printMutex.release()
                        if self.checkWinner(x, y, curTurn):
                            self.players[curTurn].conn.send(json.dumps({
                                "type": "win"
                            }).encode("utf-8"))
                            self.players[1 - curTurn].conn.send(json.dumps({
                                "type": "lose",
                                "data": {
                                    "x": szObj["data"]["x"],
                                    "y": szObj["data"]["y"]
                                }
                            }).encode("utf-8"))
                            self.gameOver = True
                        else:
                            self.players[1 - curTurn].conn.send(szBuf)
                        curTurn = 1 - curTurn
                        break
        except (ConnectionResetError, ConnectionAbortedError) as err:
            # self.players[1 - curTurn].conn.send(json.dumps({
            #     "type": "win"
            # }).encode("utf-8"))
            if clientListMutex.acquire():
                for i in range(len(clientList)):
                    if clientList[i].addr == self.players[curTurn].addr:
                        clientList.pop(i)
                        break
                clientListMutex.release()
            self.players.pop(curTurn)

    def checkWinner(self, curX, curY, role):
        i = j = 1
        while curX >= i and self.map[curY][curX - i] == role: i += 1
        while curX + j < len(self.map) and self.map[curY][curX + j] == role: j += 1
        if j + i == 6: return True

        i = j = 1
        while curY >= i and self.map[curY - i][curX] == role: i += 1
        while curY + j < len(self.map) and self.map[curY + j][curX] == role: j += 1
        if j + i == 6: return True

        i = j = 1
        while curX >= i and curY >= i and self.map[curY - i][curX - i] == role: i += 1
        while curX + j < len(self.map) and curY + j < len(self.map) and self.map[curY + j][curX + j] == role: j += 1
        if j + i == 6: return True

        i = j = 1
        while curX >= i and curY + i < len(self.map) and self.map[curY + i][curX - i] == role: i += 1
        while curX + j < len(self.map) and curY >= j and self.map[curY - j][curX + j] == role: j += 1
        if j + i == 6: return True

        return False

    def run(self):        
        self.startGame()
        for player in self.players:
            newClient = Client(player.conn, player.addr)
            if clientListMutex.acquire():
                for i in range(len(clientList)):
                    if clientList[i].addr == player.addr:
                        clientList.pop(i)
                        break
                clientList.append(newClient)
                clientListMutex.release()
            newClient.start()

class MicroGobangServer():
    
    def __init__(self):
        # self.SERVER_SOCKET = ("192.168.43.2",  8000)
        # self.SERVER_SOCKET = ("localhost",     8000)
        # self.SERVER_SOCKET = ("192.168.1.107", 8000)
        self.SERVER_SOCKET = ("192.168.1.101", 8000)
        self.sock = None
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(self.SERVER_SOCKET)
            self.sock.settimeout(None)
            self.sock.listen(10)
        except Exception as err:
            print(err)
            if (self.sock):
                self.sock.close()
            sys.exit()

    def run(self):
        print("listening...")
        clinetMonitor = ClientMonitor()
        clinetMonitor.start()
        serverInspector = ServerInspector()
        serverInspector.start()
        while True:
            conn, addr = self.sock.accept()
            conn.settimeout(None)
            client = Client(conn, addr)
            if clientListMutex.acquire():
                clientList.append(client)
                clientListMutex.release()
            if printMutex.acquire():
                print(addr, "Joined")
                printMutex.release()
            client.start()

if __name__ == '__main__':
    MicroGobangServer().run()