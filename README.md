# FaceRecognitionInRealGame
腾讯云人脸识别产品在真人实景游戏中的应用案例

## 1.案例概述
### 1.1 背景

2019年国庆，帮朋友实现了一个人脸识别进行开锁的功能，用在他的真人实景游戏业务中。几个月来运行稳定，体验良好，借着这个春节宅家的时间，整理一下这个应用的实现过程。

总的来说需求描述简单，但由于约束比较多，还是在架构与选型上花了些心思。

### 1.2 部署效果
![安装效果图](https://github.com/eckygao/FaceRecognitionInRealGame/blob/master/img/WechatIMG676.jpeg)

由于该游戏还在线上服务中，此处就不放出具体操作的视频了。

### 1.3 玩家体验

- 玩家发现并进入空间后，在显示屏看到自己在当前场景出镜的实时画面。
- 玩家靠近观察时，捕获当前帧进行人脸识别，实时画面中出现水印字幕“认证中”
- 人脸认证失败时，实时画面水印字幕变更为“认证失败”，字幕维持2秒后消失，恢复初始状态。玩家继续寻找游戏线索，重新进行认证。
- 人脸认证成功时，实时画面水印字幕变更为“认证成功”，并弹开保险箱门。进入后续游戏环节。

## 2.产品要求
### 2.1 需求说明

需求提出时比较明确，核心逻辑不复杂。

- 人脸识别：通过人脸识别进行鉴权。
- 开锁管理：通过鉴权则打开柜门，未通过则保持锁定。
- 反馈提示：需要有实时视频反馈，指引明确，便于优化玩家体验。

### 2.2 约束说明

毕竟是生意，所以在商言商，对实用性和成本要求很高，关键是不要影响游戏过程，同时保证玩家体验。

- 低成本：需要低建设成本，低维护成本。
- 易维护：对维护人员技术水平要求低，出现软硬件故障时，任意店员可以快速恢复。
- 高可靠：识别准确率高，容错能力强，系统持续运行中故障率低。
- 有限空间：整套系统在去除显示屏、电磁锁、保险箱后，其它结构实施空间不能超过20cm\*15cm\*15cm 体积。
- 采光不足：实景空间小，有顶光无侧光，曝光时间较长。
- 通用供电：只提供5V、12V两种直流电接口。
- 并行处理：鉴权流程与反馈流程并行，鉴权过程中，反馈系统不能出现中断、阻塞等情况，使玩家有明显的中断、卡死体验。
- 弱网络环境：由于房间隔断多，网络共用，所以网速有限，有突发延迟情况。

### 2.3 功能设计

可能的架构方案有多种（方案间的比较，在文末进行），下面展开说明一下最终上线的方案。

#### 2.3.1 设定流程

流程与效果，请参考 *1.3 玩家体验* 部分

#### 2.3.2 可配置内容

- 腾讯云密钥对

  修改配置文件，用于适配腾讯云账号切换功能（测试账号/正式账号）。

- 人员库ID

  修改配置文件，用于指定不同人员库（测试库/正式库）。

- 水印提示

  更换对应图片，更换水印。使用图片管理，而不是字符串配置的原因，是由于图片配置模式无需字库支持，无需配置显示大小，易于图案嵌入。由于所见即所得，对维护人员要求低。

- 关机选项

  可配置任务完成后，是否自动关机。用于游戏环境复位准备，减少复位工作量。

#### 2.3.3 运营与维护

- 系统运营管理

  场景启动时，统一上电。认证通过后，自动关机，完成复位。

- 故障处理

  软硬件故障：无法开机、可开机无显示、可开机显示系统异常，可开机未知异常等等，更换树莓派或其它硬件。
    
  网络故障：正常运行，无法认证，可查网络+查云日志，解决网络问题；
  
  云产品异常：运行4个月，未发生过，可以忽略，如发生则联系云售后；

#### 2.3.4 成本分析

- 碍件成本：500～600元。
- 备件成本：按1:1备件，500～600元。
- 运行成本：云端0元，使用免费额度；电费网费，忽略不计。

## 3.技术实现

### 3.1 系统架构

![系统架构](https://github.com/eckygao/FaceRecognitionInRealGame/blob/master/img/infrastructure.png)

#### 3.1.1 硬件组成：

![硬件组成图](https://github.com/eckygao/FaceRecognitionInRealGame/blob/master/img/hardware.png)

- 树莓派：终端主控
- 摄像头：视频输入
- 传感器：超声波测距
- 显示屏：视频输出
- 继电器：控制电磁锁
- 电磁锁：控制保险箱门

#### 3.1.2 关键特性

- 图片识别：使用图片识别，而非视频流，减少对网络带宽要求。
- 识别要求低：欠曝光照片也有高识别率。
- 触发识别：玩家在场景内活动时间长，触发模式避免了高频认证、误开锁情况，同时降低认证成本。
- 测距选型：超声波传感器技术成熟，成本低（3元）；激光传感器成本高（30元）
- 多进程：视频处理（水印提示）与认证由两个进程实现，避免了阻塞等情况，同时使用进程间通信，实现可靠交互。

### 3.2 系统搭建

#### 3.2.1 腾讯云配置

- 注册账号

  按[文档指引](https://cloud.tencent.com/document/product/598/40488)获取API密钥

- 配置人脸识别

  访问[官网控制台](https://console.cloud.tencent.com/aiface)，通过“新建人员库->创建人员->上传照片”，建立认证基础。
  
  其中所使用的“人员库ID”是关键信息，用于后续API调用识别时，指定认证动作匹配的人员库。
  
  注：由于此案例只识别一个人员，无需对人员ID进行匹配，故不用指定人员ID。

#### 3.2.2 树莓派配置

- 安装系统

  访问 [www.raspberrypi.org](https://www.raspberrypi.org/downloads/raspbian/) 获取镜像，并进行安装。注意必安装桌面版，否则需要单独管理HDMI输出。

- 配置网络

进入命令行，执行 "raspi-config"，选择"Network Options"，配置WiFi接入点。为了固定IP，编辑 /etc/dhcpcd.conf 文件，添加配置信息。

```
# 具体内容请参考你的本地网络规划
interface wlan0
static ip_address=192.168.0.xx/24
static routers=192.168.0.1
static domain_name_servers=192.168.0.1 192.168.0.2
```

- 安装依赖库

系统默认安装python2.7，但没有opencv库，需要安装。（下载包体积较大，默认源为国外站，比较慢。树莓派改国内源方法，请自行百度，并挑选离自己近的源站）

```
sudo apt-get install libopencv-dev -y
sudo apt-get install python-opencv -y
```

- 部署代码

访问[github](https://github.com/eckygao/FaceRecognitionInRealGame)获取源码，将src文件夹内容，复制到 /home/pi/faceid 下。

更改 /home/pi/faceid/config.json 中的配置信息，必须改为你的 云API密钥(sid/skey)、人员库ID(facegroupid)，其它配置按需调整。

- 配置自启动

需要配置图形界面自启动，保证视频输出由HDMI接口输出至显示屏，编辑 /home/pi/.config/autostart/faceid.desktop 写入如下内容

```
Type=Application
Exec=python /home/pi/faceid/main.py
```

#### 3.2.3 硬件接线

**树莓派GPIO图示**

![](http://www.raspberry-pi-geek.com/var/rpi/storage/images/media/images/raspib-gpio/12356-1-eng-US/RasPiB-GPIO_lightbox.png)

**摄像头**

- CSI接口

![](https://github.com/eckygao/FaceRecognitionInRealGame/blob/master/img/camera_rpi.jpg)

**超声波传感器**

- TrigPin： BCM-24 / GPIO24
- EchoPin： BCM-23 / GPIO23
- VCC ：接5V
- GND ：接GND

**继电器**

- VCC ：接5V
- GND/RGND ：接GND
- CH1 : BCM-12 / GPIO12

#### 3.2.4 测试运行

完成上述工作后，接电启动系统，本地反馈查看显示屏，云端识别结果可查看[系统日志](https://console.cloud.tencent.com/aiface/search-face/history)。

### 3.3 代码逻辑与涉及技术

#### 3.3.1 流程伪代码

```
# 监测鉴权进程-主进程
获取应用配置（API ID/Key 等）
初始化GPIO针脚（端子）
启动视频管理进程（辅进程）
循环开始：
  if not 测距达到触发标准:
    continue
  与辅进程通信（捕获当前帧，并存入指定路径，并添加“检测中”水印）
  调用云API，使用该帧图片人脸识别
  if 识别成功:
    与辅进程通信（变更水印为“检测成功”）
    等待5秒
    关机 或 继续运行（由config.json中 su2halt 字段指定）
  else：
    与辅进程通信（变更水印为“检测失败”）
    等待2秒
  与辅进程通信（清除水印）

# 视频管理进程-辅进程
初始化摄像头
循环开始：
  取帧
  取进程间共享队列
    按消息进行不同操作（帧图像保存/加不同水印/不处理）
  输出帧
```

#### 3.3.2 视频与图像

- 实时视频

  如上文伪代码所示，通过逐帧处理，并连续输出，显示实时视频。
  
- 触发识别

  测距传感器确认物体靠近，且0.3秒内距离变化小于2cm，确认为待认证状态。再延时0.3秒，进行图像帧捕获。再次延时的原因是物体停止时，会有扭转、微调等动作，若直接取帧，会由于采光不足（上文提到的约束）出现模糊情况，所以再次延时，确保捕获稳定图像。
  
- 人脸识别

  请参考[文档介绍](https://cloud.tencent.com/product/facerecognition)。

#### 3.3.3 水印添加

- 水印原理

  opencv中，提供了多种图像处理函数，如：图文处理（图加字）、图图处理（图间加/减/乘/除/位运算）等等。通过不同的处理方式，可以实现 底图加字、底图加图、掩膜处理等等多种效果。本案例中使用的是基于位运算的掩膜处理方式。

- 水印图片

  为了便于维护和更新，本案例中使用图片做为水印来源，避免字库约束，也增大了灵活性，易于在水印中增加图形，并以分辨率直接定义水印大小，所见即所得。
  默认水印图片为白底黑字。

- 水印处理逻辑

  为突出水印的浮动效果，将水印图片中的黑色区域透明化后，叠加到原始图片中。由于字体透明效果，水印字体颜色随基础视频变化，效果比较明显。
  
  源码说明
  
```
# img1为当前视频帧（底图），img2为已读取水印图
def addpic(img1,img2):
    # 关注区域ROI-取原图中将被水印图编辑的图像
    rows, cols = img2.shape[:2]
    roi = img1[:rows, :cols]

    # 图片灰化-避免改动图非纯黑纯白情况
    img2gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    # 生成掩膜-过滤浅色，位运算取非
    ret, mask = cv2.threshold(img2gray, 220, 255, 3) #cv2.THRESH_BINARY
    mask_inv = cv2.bitwise_not(mask)

    # 生成水印区图像-底图裁出字体部分，生成水印区最终图像，替换原图水印区
    img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
    dst = cv2.add(img1_bg, img2)
    img1[:rows, :cols] = dst
    return img1
```

示意效果图（示意图扩大水印区，用于突出效果，实际应用方案中水印区较小）

![水印效果图](https://github.com/eckygao/FaceRecognitionInRealGame/blob/master/img/re_test.jpg)

#### 3.3.4 硬件相关

- 超声波测距

  超声波传感器（4引脚：VCC、Trig、Echo、GND）,Trig端输出一个大于10μs的高电平，激活发波，在收波后，Echo端会输出一个持续高电平，持续时间就是发出超声波，至收到超声波的时间。即：测距结果(米)=时长*340米/2

- 继电器

  5V继电器模块有两侧接线，一侧为供电与信号（4引脚，兼容3.3V信号），一侧为通路开闭管理（3端口）。电磁锁供电默认接继电器常闭端，对继电器给出信号后，切换为常开状态，则电磁锁断电开锁.

- GPIO

  GPIO（General-purpose input/output 通用输入输出），以引脚方式提供硬件间的联系能力。树莓派 3B+，有40个GPIO引脚（请参考 *3.2.3 硬件接线* 中的参考图示），树莓派官方操作系统 Raspbian 下，可以使用系统默认安装的 python 中 RPi.GPIO 库，进行操作。 

## 4.其它

### 4.1 方案选型对比

设计的核心在于人脸鉴权模块，这里直接影响成本和稳定性，最后选择了上文方案（平衡成本、维护性及可靠性）。曾经的其它几种备选人脸识别方案：

#### 4.1.1 本地识别A方案：

使用ESP-EYE芯片，均由芯片完成，依赖ESP-IDF、ESP—WHO，使用C进行开发。

低硬件成本（模块成本189\*2），高开发维护成本（C开发）。

问题：难于更新配置与故障分析处理。适用于大量部署场景。

#### 4.1.2 本地识别B方案：

使用树莓派直接进行人脸识别，方案成熟，开源代码丰富。

中硬件成本，低开发成本，高维护成本。

问题：树莓派负载高，即使用间隔帧算法，也仅维持在20fps以下，卡顿明显。如进一步调优，受限于个人经验问题，恐难以保持长期稳定运行。

#### 4.1.3 本地识别C方案：

使用 BM1880边缘计算开发板 或其它图像处理板，社区口碑不错，有框架支持。

问题：高硬件成本（模块成本1000\*2），高开发维护成本(C开发)。如果使用算力棒，需要X86_64做基础平台，成本降低有限，复杂度不变。适用于扩展能力场景。

#### 4.1.4 云端识别A方案：

使用腾讯云的[视频智能分析](https://aivideo.cloud.tencent.com/list.html)产品，简化终端架构，使用树莓派zero推流上云（后续放出实现方案），即可获取识别结果，且支持高频多次检索等特性。

部署成本低（终端视频相关模块150元），运营成本低（当前0.28元/分钟，按该场景下单次运行20分钟计算，单次游戏成本5.6元）

问题：对网络稳定性依赖大，断流等情况影响体验。在本案例的网络约束下，影响使用效果，更适于网络条件较好、高频检索的应用场景。
