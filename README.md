[TOC]  

<font face=宋体 size=3>程序已上传到我的Github上：<a href="https://github.com/ThomasAtlantis/MicroGobang" target="new">MicroGobang</a></font>
<font face=宋体>  
### 1 贪吃蛇游戏的调试分析  
</font><font face=宋体 size=3>
贪吃蛇是一款非常经典的游戏，常作为软硬件入门级的开发项目。本次实验对资料中的贪吃蛇例程进行运行和调试，目的是熟悉`Skids`的硬件结构，熟悉`MicroPython`语法及其对`Skids`硬件资源的调用接口。  
</font><font face=宋体>
#### 1.1 硬件结构  
</font><font face=宋体 size=3>
<div align="center"><img src="/uploads/kindeditor/2019/5/5a32aaec-7e04-11e9-931b-00163e0c3e76.jpg" width="40%" height="" /></div>  
图1-1 `Skids`开发板实物图  
  
查询`Skids`开发板的文档并进行实验分析可以得到其硬件配置如下：  

+ 嵌入式处理器为ESP32双核32位MCU，主频高达230MHz，计算能力可达600DMIPS，支持`MicroPython`编程开发  
+ 集成了WIFI和蓝牙功能；并可以扩展支持Zigbee协议  
+ 搭配了2.8寸高清液晶屏，液晶屏的像素为240像素x320像素  
+ 集成了4个按动键和4个触摸键  
+ 提供了Micro USB接口，可以与PC连接，支持串口通信和程序下载  
+ 提供了3.5mm音频接口，未集成模块，目前还不能用  
+ 提供了TF卡插槽，支持TF卡，目前还不能用  
+ 提供了电池电源预留端口，但不支持其他引脚扩展  
+ 提供了4个LED灯，在按键按下时电平触发点亮，但由于焊接失误，不支持程序控制LED的亮灭  

注意板子的方向，默认如图1-1所示，对应的按键信息见表1-1。  
  
表1-1 `Skids`的按动键与LED对应信息表  
  
|按键ID|方向|LED ID|颜色|  
|---|---|---|---|  
|S1|下|V4|红|  
|S2|左|V5|绿|  
|S3|上|V6|蓝|  
|S4|右|V7|黄|  
  
贪吃蛇程序使用4个按动键作为方向键控制蛇的移动方向，使用液晶屏显示游戏场景，使用Micro USB接口下载程序。  
</font><font face=宋体>
#### 1.2 软件结构  
</font><font face=宋体 size=3>
贪吃蛇游戏使用面向对象的思想开发，将程序划分为若干类：  

+ 格栅系统类（Grid）。将屏幕划分为若干等大的正方形格子，在初始化时绘制游戏场景的边框和背景。提供draw方法使用指定颜色填充指定位置的格子。  
+ 食物类（Food）。在屏幕随机的一个格子绘制食物。  
+ 蛇类（Snake）。在构造函数中初始化蛇身位置、颜色、移动方向等，提供了控制蛇向指定点移动一格的方法，以及三种吃到特殊食物时蛇身的变化特效。  
+ 游戏类（SnakeGame）。控制游戏的初始化，食物的产生，蛇身的移动和增减以及按键对方向的控制。游戏的大体流程如图1-2所示。  

<div align="center"><img src="/uploads/kindeditor/2019/5/5a4f0cbe-7e04-11e9-9207-00163e0c3e76.jpg" width="90%" height="" /></div>   
图1-2 贪吃蛇游戏活动图  
</font><font face=宋体>
#### 1.3 调试升级  
</font><font face=宋体 size=3>
经过运行和调试，发现了程序中存在若干漏洞，下面将简要说明这些漏洞、出现场景及修复的办法。  

**BUG_1**:蛇身长度小于3时也可能吃到减二食物，最终蛇长变为1。出现场景：蛇长超过10后，遇见减二白块，先撞死自己，蛇身变为3，再吃白块。修复方法：每次游戏结束后都在蛇身初始化后重新生成食物  

**BUG_2**: 蛇从左向右穿过右墙时，和墙间隔1格时即穿墙。出现场景：蛇从左向右穿过右墙时。修复方法：这是由于self.grid.width实际是能取到的，修改向右移动逻辑：`new = ((head[0] + 1) % (self.grid.width + 1), head[1])`  

**BUG_3**: 长按与蛇前进方向相同的方向键，可以达到二倍速。出现场景：长按与蛇前进方向相同的方向键，在key_release函数中多调用了1次move()。修复方法：虽然这不是bug，但想修复，可以在key_release屏蔽按键时屏蔽掉同方向  

**BUG_4**: 无论如何按键蛇都不能贴着身体掉头，两次转向间隔了一个方块。出现场景：连按两次同方向转向键，蛇头与蛇身隔了一行。修复方法：产生原因同**BUG_3**中描述的问题：按键会触发一次move。去除key_release中的move，为了保留二倍速效果，判断按键同方向时，调用move()  

**BUG_5**: 程序中含有暂停逻辑，但游戏并不能暂停。修复方法： 按键太少了，那就把暂停功能去了呀，提高性能。  

**BUG_6**: KeyInterupt后重新下载会崩溃。一开始猜想这是因为键盘中断导致了现场没有恢复到原始状态，后来发现程序运行久了也会崩，猜想是垃圾回收机制有问题。最后研究结论是我优化原有代码引入了Python的enumerate函数，但`MicroPython`实际支持效果不好，只需要使用其他方式替代enumerate即可。  

其他不足之处。这篇代码为了提高可复用性和易修改性，将诸如格栅大小等参数封装起来，但实际使用到这些变量时，仍然使用的是常数，前后不统一，没有达到应有效果。在程序中还使用了如字符串字典等开销较大的结构，按键事件的扫描逻辑处代码冗余且可读性差。诸如此类问题很多，在注释过程中进行了一一修改，最终版见附件程序。  
</font><font face=宋体>
### 2 网络模块调试与应用  
#### 2.1 WiFi与socket测试  
</font><font face=宋体 size=3>

`Skids`开发板既可以作为WiFi的AP，也可以连接入现有的WiFi。本次实验主要尝试了后者。参考网上给出的关于ESP32连接WiFi的教程，经过适当修改，得到一个可用的程序：  
```python
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
```

我们只需要将WiFi的名称和密码传入函数即可连入WiFi。根据官方文档中的资料，我们可以使用usocket库进行socket编程，实现点对点的TCP协议的通信。我编写了一个测试程序，使用`Skids`做为socket客户端，使用PC机作为服务器，这里需要两台机器连入同一个局域网。测试程序见附件。  

<div align="center"><img src="/uploads/kindeditor/2019/5/5a6defee-7e04-11e9-b2c8-00163e0c3e76.png" width="90%" height="" /></div>
<div align="center"><img src="/uploads/kindeditor/2019/5/5a8c763a-7e04-11e9-a255-00163e0c3e76.png" width="90%" height="" /></div>  
图2-1 WiFi与Socket测试结果截图  
</font><font face=宋体>
#### 2.2 PC键盘控制的贪吃蛇  
</font><font face=宋体 size=3>

本实验将原有的贪吃蛇游戏的键盘扫描功能加以改造，将`Skids`开发板连入WiFi并作为socket服务器端，将PC机作为客户端。PC机与`Skids`建立socket连接之后，用户按下键盘方向键将会发送特定的消息给`Skids`，控制上面运行的贪吃蛇的方向。程序见附件。  
运行方法：将SkidsServer.py烧写入`Skids`开发板中，然后在PC端启动PCClient.py，使用方向键即可控制蛇的方向。  
</font><font face=宋体>
### 3 触摸按键、文件和图像功能测试  
#### 3.1 触摸按键  
</font><font face=宋体 size=3>

由于官方文档中没有给出触摸板的引脚号，所以需要编写程序进行测试。将所有引脚的电压值定时读取出来，按下触摸按键时，发现对应引脚的电压会下降，从而找到了触摸按键和引脚号的对应关系。官方提供了封装触摸板的TouchPad类，它的read()方法可以得到对应电压值。对实验结果进行分析，我们可以设置500作为按键是否被触摸的阈值。   

表3-1 触摸按键与引脚对应表

|触摸按键ID|引脚号|
|---|---|
|SW5|TouchPad(Pin(27))|
|SW4|TouchPad(Pin(33))|
|SW3|TouchPad(Pin(32))|
|SW2|TouchPad(Pin(4))|
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5aa20e6e-7e04-11e9-8b60-00163e0c3e76.png" width="80%" height="" /></div>   
<div align="center"><img src="/uploads/kindeditor/2019/5/5ab8a2a0-7e04-11e9-87fc-00163e0c3e76.png" width="80%" height="" /></div>  
<div align="center"><img src="/uploads/kindeditor/2019/5/5acbf8c8-7e04-11e9-8a31-00163e0c3e76.png" width="80%" height="" /></div>  
<div align="center"><img src="/uploads/kindeditor/2019/5/5ae3c5b6-7e04-11e9-876a-00163e0c3e76.png" width="80%" height="" /></div>

图3-1 触摸按键扫描测试截图  
</font><font face=宋体>
#### 3.2 文件功能  
</font><font face=宋体 size=3>

`Skids`支持JSON和INI格式的文件下载，两个文件都可以作为参数配置文件。由于`Skids`的ujson库支持JSON字典与字符串的互相转换，故推荐使用JSON。在`MicroPython`中可以直接使用open语句读写文件。  

<div align="center"><img src="/uploads/kindeditor/2019/5/5b04ce50-7e04-11e9-b76b-00163e0c3e76.png" width="90%" height="" /></div>   
图3-2 读取JSON文件实验截图  
</font><font face=宋体>
#### 3.3 图像功能  
</font><font face=宋体 size=3>

由于开发板不支持图片格式的文件，故尝试将图片的RGB像素值直接编码入程序源码中。首先对图片进行了压缩，使其大小为240像素x320像素，以适应屏幕大小。使用drawline的方式绘制每个像素点。程序下载时发生崩溃，PC机蓝屏。这是因为`Skids`支持的程序堆栈区其实是很小的，程序超长导致崩溃。  
使用以下指令可以得到`Skids`的内存信息。  
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5ba31b3c-7e04-11e9-bc3a-00163e0c3e76.png" width="80%" height="" /></div>
图3-3 `Skids`内存堆栈信息  

可以看到`Skids`支持15KB的栈和108.5KB的堆。显然程序中储存的像素数组是开辟在栈区的，不考虑列表数据结构带来的额外开销，也不考虑python中整型数的动态长度，假设RGB值为3个4Byte的整型数，那么上面一幅图片需要：`240 x 320 x 3 x 4 / 1024 = 900KB`  

除此之外，代码在运行时还需要占用内存，python解释器和操作系统也要占用内存，所以无论如何也会内存溢出。  

那么我们应该将图片以二进制的格式编码存储在EEPROM中，然后使用open函数每次加载一部分像素信息进入内存，更新屏幕绘制后释放，重新读入下一部分。由于官方文档在实验结束后进行了更新，可以看到，官方文档中使用ubitmap.BitmapFromFile方法读取位图图像，应该是对这个过程的封装。  
</font><font face=宋体>
### 4 五子棋联机对战系统设计  
#### 4.1 系统结构设计 
</font><font face=宋体 size=3> 

云端：使用一台阿里云服务器，搭建了Python3的运行环境，在后台运行系统的服务器端程序。服务器端主要负责监控客户端的接入，检查用户口令，在口令相同的客户端列表中随机选取两个用户进入房间。接收用户的落子或投降消息，检查游戏的输赢。  

`Skids`：客户端程序负责游戏界面的显示、跳转，用户按键输入的检测，游戏流程逻辑，用户输入的合法性检测。  

游戏整体流程见图4-1，图中没有包括投降功能。首先启动服务器端程序。其后用户打开`Skids`开发板，进入口令输入界面，使用方向键输入一串口令，进入等待匹配对手的阻塞状态。当两台及以上具有相同口令的客户端连入系统，其中随机两台将会进入同一个游戏房间，客户端跳转到棋盘界面，同时系统为双方分配黑白，黑方先行。在棋局回合正常轮换时，当前回合用户可用方向键调整光标位置，用触摸板确认，也可以用触摸板指定按键发起投降。对方用户将进入阻塞状态，无法移动光标。若用户发起投降，或服务器端检测棋局结束，双方的客户端将会显示输赢信息，一段时间后跳转回口令输入界面，重新开始游戏；否则棋局正常进行，将在双方客户端显示当前落子，并交换棋权。  
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5bc3145a-7e04-11e9-8917-00163e0c3e76.jpg" width="80%" height="" /></div>
图4-1 五子棋联机对战游戏整体流程  
</font><font face=宋体>
#### 4.2 系统硬件设计 
</font><font face=宋体 size=3> 

客户端使用`Skids`开发板，使用集成好的WiFi模块连入互联网，使用液晶显示屏显示游戏场景，使用按动键和触摸键与游戏进行交互。具体的按键配置如下：  

（1）口令输入界面键位  
4个方向键 -- 输入口令  
触摸键SW2 -- 清空输入  
触摸键SW5 -- 匹配对手  
触摸键SW3 -- 退出游戏  

（2）对局室界面键位  
4个方向键 -- 移动光标  
触摸键SW5 -- 确认落子  
触摸键SW2 – 发起投降  
</font><font face=宋体>
#### 4.3 系统软件设计 
</font><font face=宋体 size=3> 

（1）服务器端  

服务器端维护的数据结构见图4-2。维护客户端列表，即空闲连接池，包含了所有连入系统的客户端，以及和它们通信所必须的信息，如IP地址、端口、时间戳等。维护口令字典，key为客户端发来的口令，value为客户端的指针列表，包含了具有相同口令的一组客户端的指针。维护房间列表，包含了不同游戏房间，每个房间包含两个游戏玩家，即两个客户端的指针。为了实现非阻塞的socket连接，服务器端应用了多线程技术。以上三种数据结构会在不同的线程中访问，故需加锁，并考虑避免死锁现象。  
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5c0928c8-7e04-11e9-9b61-00163e0c3e76.png" width="70%" height="" /></div>
图4-2 服务器端数据结构  

主线程：监听客户端的接入，当有新的客户端接入时，开启客户端线程  

客户端线程：初始化函数中将客户端加入空闲连接池。监听客户端发送来的消息，当客户端发来动作为token的消息时，将客户端的指针插入口令字典。  

客户端监控器：每隔一定时间，检查口令字典中每个口令对应的客户端列表。当列表长度超过2时，随机pop出其中两个，开启游戏房间线程，将两个客户端作为玩家双方加入房间。若列表长度为0，需“清理垃圾”，将口令从字典中删除。  

游戏房间线程：初始化时为玩家分配角色。控制客户端游戏的同步，接收落子和投降信息，检测游戏结束条件，并将游戏结束信息或新的落子信息发送给下一回合玩家。  

这样在游戏开始时，系统调用过程为：主线程->客户端监控器->有客户端接入时：客户端线程->口令匹配时：游戏房间线程。在游戏结束后，游戏房间线程死亡，客户端线程仍然处于检测口令循环，而口令字典中已pop掉对应玩家，故系统回复到了初始状态，可以重新游戏。  

（2）客户端  

客户端实现功能并不难，但由于`Skids`对很多功能没有提供封装，程序主要关注封装、解耦与复用。程序设计了Key, TouchKey, PressKey, CFG, CSS, Label, Canvas, ChessboardUnit, Chessboard和MicroGobangClient共10个类。  

关于按键封装。设计抽象类Key，泛化出触摸键TouchKey与按动键PressKey，实现了keyDown方法，用以检测按键是否被按下，使用边沿检测取代电平检测，并加入了按键消抖。这样封装将系统中的按键统一起来，只需调用其keyDown方法而不需考虑是何种按键，以及如何实现检测。需要判断按键类型时，只需要使用Python自带的isInstance方法，判断对象是哪个类的实例即可。  
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5c1f8d16-7e04-11e9-bb75-00163e0c3e76.png" width="20%" height="" /></div>
图4-3 按键类图  

关于配置信息封装。CFG类实现了从JSON文件中加载配置信息，使用特殊的__call__方法使实例本身可作为函数使用，用于获取指定键的对应的值。CSS类继承了CFG类，用于从样式表文件加载元素的样式，在__call__中加以改进，如增加字符串型RGB值向整型RGB值的转换，以适应绘图函数的调用接口。  
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5c6b3e32-7e04-11e9-b944-00163e0c3e76.png" width="20%" height="" /></div>
图4-4 配置信息类图  

关于绘图工具封装。画布类Canvas是对`Skids`标准库screen类的增强，提供了屏幕大小对绘图的控制，支持清屏、绘制直线、绘制空心和实心矩形、绘制光标矩形等方法，使接口调用更方便简短。  

关于标签控件封装。标签类Label是模拟HTML语言中的元素的一次尝试。可以通过初始化函数传参控制样式，可与CSS类配合，包含了样式的具体实现。可设置标签文字和清空标签内容。  

关于棋盘封装。棋盘的每个小格封装为ChessboardUnit类，提供了对应位置落子、获得焦点和失去焦点的图形绘制。Chessboard类维护整个棋盘的地图数组，提供了棋盘的绘制，移动光标和落子等功能，包括了边界检测越界循环。  

<div align="center"><img src="/uploads/kindeditor/2019/5/5c7e7934-7e04-11e9-8462-00163e0c3e76.png" width="20%" height="" /></div>   
图4-5 棋盘类图  

MicroGobangClient是客户端游戏的主类，负责整体游戏逻辑，下分为3个函数实现的页面：欢迎页、口令输入页和对局室页，通过run方法调用。程序还对网络接口进行了适当封装，使用JSON消息格式，用type指明消息类型，用data给出消息体内容。整体来看，具有绘图功能的类与Canvas为单向关联，标签元素与CSS样式表为印记耦合，其他的类都是在游戏主类中顺序调用，之间很少产生联系。所以系统不同模块的耦合度较低，而Canvas、Label、CSS、Key等模块都可以直接复用。  
   
<div align="center"><img src="/uploads/kindeditor/2019/5/5c924748-7e04-11e9-b0ad-00163e0c3e76.png" width="40%" height="" /></div>
图4-6 游戏界面逻辑  
</font><font face=宋体>
#### 4.4 系统遗留问题 
</font><font face=宋体 size=3> 

（1）连接中断异常  

实验后期主要致力于解决客户端由于突发事件下线的异常。在现有逻辑下，客户端掉电将会导致系统进入不确定状态（跑飞）。由于Python不支持socket连接的活性检验，所以需要自己尝试。心跳包维护长连接的方式必须在客户端和服务器间增加一道连接，这对客户端的多线程能力和网络带宽都有要求，逻辑复杂并且较为耗电，故该方法被排除。  

经过在PC机上模拟客户端反复试验发现，在客户端按键中断或者直接退出时，会在服务器端引发ConnectionResetError或ConnectionAbortedError异常。于是针对客户端掉线的不同时机，加入了对口令输入前掉线、口令输入中掉线、和对局掉线等全方位异常处理。问题解决后，使用`Skids`开发板调试，发现以上努力是徒劳的，`Skids`掉电不会再服务器端引发任何反应。  

这是一个遗留问题，还需进一步研究。以上尝试虽无法解决问题，但给出了不同情况下客户端掉线的应对逻辑，可供参考。后来官方文档进行了更新，给出了MQTT协议，以及多线程的例子，可能对这个问题有帮助。  

（2）匹配对手时无法退出游戏  

如果问题（1）解决了，那么当然可以直接关闭电源。否则，匹配对手时客户端会阻塞，如果长时间匹配不到对手也将无法重新开始，这是系统的一个漏洞。可以尝试使用多线程的方式解决。  

（3）WiFi的SSID和密码无法从外部更改  

如果想将开发板产品化，那么必须支持在不烧写程序情况下即可改变连入WiFi的信息，否则WiFi环境变化，客户端不能入网。可以考虑设置某个按键使`Skids`进入配置模式，用户可以通过手机或PC机无线修改参数。如果使用蓝牙，应将其设置为Slave模式，如果使用WiFi，应将其设为AP。  

（4）可预留某个口令作为人工智能接口  

在服务器端加入人工智能逻辑，在用户输入口令与其口令对应时，即可与人工智能对弈。这是一个有待开发的功能。  
</font><font face=宋体>
#### 4.5 运行方式说明 
</font><font face=宋体 size=3> 

本地测试时，PC端在cmd中使用ipconfig命令查看无线局域网的Ipv4地址。在server.py中配置SERVER_SOCKET的值为Ipv4地址和自定义的端口（端口不要和其他程序冲突，建议为8000），然后运行server.py，可看到listening...提示信息，服务器进入连接监听状态。  

在cfg.json中配置与PC端接入的WiFi相同的SSID和密码，将SERVER_IP和SERVER_PORT设为刚刚PC端设置的值。将cfg.json、css.json和main.py烧写进`Skids`中，上电运行，可看到输出信息提示wifi已连接和socket已连接。连入两块`Skids`开发板，在输入口令时输入相同口令，即可开始游戏。  
若要在云端部署，只需在执行上述步骤时，将服务器端的IP和端口设为服务器的外部IP以及入站规则中允许的端口。而客户端只需选用任意可入网的WiFi即可。  
</font><font face=宋体>
### 5 心得与建议  
</font><font face=宋体 size=3>

（1）`MicroPython`与Python不同。前者只是后者的一个子集，但让人想吐槽的是，没有找到一个详细的文档讲述两者具体哪里不同。使用Python的语法在`MicroPython`的处理器上编译可以通过，但偶尔会出问题，很难调试，比如生成器语法enumerate。  

（2）液晶屏真的怕压。板子的下表面有保护，但上表面没有，所以装在书包里轻轻松松就压坏了。  

（3）python的局限性。Python其实适合做数据分析和处理类的小实验，不适合做大型的产品。Python的按键检测真的很差，C语言_getch()函数一行的问题，python需要写几十行，还要借助第三方库。Python的socket连接还不能检测活性，所以在很多方面，Python并不是强项。  

（4）`Skids`板子的内存真的很小，官方文档不全面，外设不能扩展，图形接口很单一（turtle画圆画不圆），开发起来感觉很鸡肋。但这个板子的定位本来就不是做游戏的，期待它能越来越好吧  
</font><font face=宋体>
### 7 参考资料  
</font><font face=宋体 size=3>

+ [1] Skids快速参考，<a href="https://skidsdocs.readthedocs.io/zh_CN/latest/skids/quickref/skidsintro.html" target="new">https://skidsdocs.readthedocs.io/zh_CN/latest/skids/quickref/skidsintro.html</a>   
+ [2] MicroPython-ESP32之更合理的建立wifi连接-1Z实验室，<a href="https://www.jianshu.com/p/0613f3f3f4ba?tdsourcetag=s_pctim_aiomsg" target="new">https://www.jianshu.com/p/0613f3f3f4ba?tdsourcetag=s_pctim_aiomsg</a>   
+ [3] MicroPython入坑记（一）（ESP8266 ESP32），<a href="https://www.cnblogs.com/yafengabc/p/8680938.html" target="new">https://www.cnblogs.com/yafengabc/p/8680938.html</a>   

</font><font face=宋体>
### 6 文件结构  
</font><font face=宋体 size=3>

注：程序注释主要参考”./sourceCode/MicroGobang/正式发布/”中的程序  

```python
├─"document"  
│      "General.jpg"  
│      "GreedySnake.jpg"  
│      "ServerDataStructure.jpg"  
│  
└─"sourceCode" # 附件A：源程序  
    │  "GreedySnake.py" # 贪吃蛇注释  
    │  "ImageCompress.py" # 图片压缩  
    │  "TouchPadScan.py" # 触摸板扫描测试  
    │  
    ├─"GreedySnakeControlledByPC" # PC端控制Skids贪吃蛇  
    │      "PCClient.py" 
    │      "SkidsServer.py" 
    │  
    ├─"JSONFileTest" # JSON格式文件功能测试  
    │      "JOSNFileTest.py" 
    │      "params.json"  
    │  
    ├─"MicroGobang" # 五子棋联机对战系统  
    │  ├─"修复尝试" # 修复连接中断异常的尝试  
    │  │      "cfg.json"  
    │  │      "css.json"  
    │  │      "main_simulation.py" # PC端模拟Skids客户端  
    │  │      "main_test.py" # Skids端客户端  
    │  │      "run_main_test.bat" # 运行模拟的批处理程序，可忽略  
    │  │      "server_test.py" # PC端服务器  
    │  │  
    │  └─"正式发布" # 第一个可用的系统  
    │          "cfg.json"  
    │          "css.json"  
    │          "main.py" 
    │          "server.py" 
    │  
    └─"WiFiSocketTest" # WiFi和Socket编程的测试  
            "PCServer.py" 
            "SkidsClient.py" 
```
</font>