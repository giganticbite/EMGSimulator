# coding:utf-8

# @package classSerial
#
#	シリアルポートクラス
#

import serial
import struct


# テスト接続用の BaudRate 固有設定を使用するか？
#	0:	1000000　固定モード
#	1:	115200
testConnectModeOn = 0


# シリアルポート管理クラス
#
#		シリアルポートに関する処理を扱う
#
#
class SerialPort(object):

    # コンストラクタ
    #
    #	@return		なし
    #	@param		self 		The object pointer.
    def __init__(self):

        # ポートへのアクセスパス
        self.mDeviceName = "COM16"
        # self.mDeviceName = "COM3"
        # ハンドル
        self.mHandle = 0
        # タイムアウト(second)
        self.mTimeOut = 3
        # 確認用コンソール出力フラグ
        self.isPrintLog = False
        # Baudrate値
        if testConnectModeOn == 0:
            self.mBaudRate = 3000000
        else:
            self.mBaudRate = 115200

    # クラスが有効か?
    #	@return		boolean		True シリアルポートへのアクセスが可能		False	それ以外
    #	@param		self 		The object pointer.

    def isEnableAccess(self):
        if self.mHandle != 0:
            return True
        else:
            self.printLog("Not Open port:" + self.mDeviceName)
        return False

    # ポートへのアクセス開始
    #		timeout値,baudrateの変更などを行う場合は、portOpenの前に変更しておく必要あり
    #
    #	@return		boolean		True シリアルポートへのアクセスが可能		False	それ以外
    #
    #	@param		self 		The object pointer.
    #	@param		portName 	ポートへのパス
    def portOpen(self, portName):
        self.mDeviceName = portName
        try:
            self.mHandle = serial.Serial(
                self.mDeviceName, self.mBaudRate, timeout=self.mTimeOut)
            print("port Open Success!:" + self.mDeviceName)
        except serial.serialutil.SerialException:
            # 例外が発生
            pass
            self.printLog("Error portOpen() :" + portName)
        # else:
        #	self.mHandle.open()

    # ポートへのアクセス終了
    #
    #	@return		なし
    #	@param		self 		The object pointer.

    def portClose(self):
        if self.isEnableAccess() == True:
            self.mHandle.close()
            print("port Close Success!:" + self.mDeviceName)
            self.mHandle = 0
        else:
            self.printLog("not Open Port:" + self.mDeviceName)

    # パケットの送信
    #
    #	@return		なし
    #	@param		self 				The object pointer.
    #	@param		sendPacketByte 		シリアルポートへ送信するパケット
    def sendPacket(self, sendPacketByte):
        if self.isEnableAccess() == False:
            return

        # 送信
        self.mHandle.write(sendPacketByte)
        self.printLog("send:" + sendPacketByte.hex())

    # パケットの受信
    #		受信バイト数を指定して読込
    #	@return		受信したパケット
    #	@param		self 				The object pointer.
    #	@param		readByteSize 		読込バイト数
    def receiveBufferSync(self, readByteSize):
        if self.isEnableAccess() == True:
            receivePacket = self.mHandle.read(readByteSize)
            logStr = "receiveSync : " + receivePacket
            self.printLog(logStr)
            return receivePacket
        else:
            return 0

    # パケットの受信
    #		受信バッファにたまったものを随時読込
    #	@return		受信したパケット
    #	@param		self 				The object pointer.

    def receiveBufferASync(self):
        if self.isEnableAccess() == True:
            nowBufferSize = self.mHandle.inWaiting()
            if 0 < nowBufferSize:
                receivePacket = self.mHandle.read(nowBufferSize)
                #logStr = "receive : " + str(nowBufferSize) + "bytes :" + receivePacket
                #logStr = "receive : " + str(nowBufferSize) + "bytes :" + receivePacket.decode('utf-8', 'replace')
                #logStr = "receive : " + str(nowBufferSize) + "bytes :" + str(int.from_bytes(receivePacket, "big"))
                # if receivePacket.hex()[10]=="8" and receivePacket.hex()[11]=="3":
                #	logStr = round(struct.unpack_from(b'>f',receivePacket,11)[0],2)
                #	logStr = str(logStr) + "  " + receivePacket.hex()
                # else:
                #    logStr = "receive : " + str(nowBufferSize) + "bytes :" + receivePacket.hex()
                # print(logStr)
                # self.printLog(logStr)
                return receivePacket

        return 0

    # パケットの受信
    #		ポートの設定確認
    #	@return		なし
    #	@param		self 				The object pointer.

    def printSetting(self):
        if self.isEnableAccess(self) == True:
            nowDic = self.mHandle.getSettingsDict()
            print("setting:" + nowDic)

    # 確認用コンソール出力
    #		isPrintLog　が有効なときにのみ、コンソール出力
    #	@return		なし
    #	@param		self 				The object pointer.
    def printLog(self, strLog):
        if self.isPrintLog == True:
            print(strLog)

    # BaudRateの設定
    #	portOpen前に設定する必要あり
    #	@return		なし
    #	@param		self 			The object pointer.
    #	@param		baudrate		baudrate値
    def settingBaudRate(self, baudrate):
        self.mBaudRate = baudrate
