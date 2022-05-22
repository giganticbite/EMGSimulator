# coding:utf-8
#
# @package classPacket
#
#		送受信パケット管理
#		送信コマンドの生成
#		受信コマンドの解析
#
#	バイトオーダー	すべてビッグエンディアン
#


from struct import *  # for pack
import datetime
import struct


#
#	定義変数	セクション
#
# プロダクトID定義
DEF_PRODUCT_ID_WirelessMotionSensor9Axis = "\x01"
DEF_PRODUCT_ID_WirelessEMGLogger = "\x02"
DEF_PRODUCT_ID_WirelessMotionSensor9Axis5G = "\x03"
DEF_PRODUCT_ID_AllDevice = "\xff"

# コマンドID	定義(必要に応じて追加)
DEF_SENDCOMMAND_ID_GETSTATUSINFO = 5
DEF_SENDCOMMAND_ID_PREMEASURE = 31
DEF_SENDCOMMAND_ID_STARTMEASURE = 2
DEF_SENDCOMMAND_ID_ENDMEASURE = 4
DEF_SENDCOMMAND_ID_SETTIMER = 12

# ACKステータス(必要に応じて追加)
DEF_ACKSTATUS_CODE_SUCCESS = '\x21'  # コマンド正常
DEF_ACKSTATUS_CODE_IMPOSSIBLE_CREATEFILE = '\x64'  # ファイル作成不可

#	グローバル変数定義	セクション

# 共通プロダクトID
#	実行中に、頻繁に変更される変数ではないので、
#	このスクリプト内で管理する
#	基本的に、起動時のみに設定
gProductId = ord(DEF_PRODUCT_ID_AllDevice)
#gProductId = ord(DEF_PRODUCT_ID_WirelessEMGLogger)

#
#	関数定義
#
#


# プロダクトIDの設定
#	@return		なし
#	@param		prodId	:	プロダクトID
def setProductID(prodId):
    gProductId = prodId

# プロダクトIDの取得
#	@return		プロダクトID
#	@param		なし


def getProductID():
    return gProductId


# bccの計算
#
#		コマンド番号から　bcc直前バイトまで
#	@return		int		数値
#
#	@param		payload		:チェック対象バッファ
#	@param		startIdx	:チェック開始要素index
# 	@param		length		:チェック長
def checkBCC(payload, startIdx, length):
    bcc = 0

    loop_i = startIdx
    while loop_i < startIdx+length:
        #		val = ord(payload[loop_i])
        val = payload[loop_i]
        bcc ^= val
        #print("bcc  val:",bcc,":",val)
        loop_i += 1
    return bcc


# 文字列→数値変換
#		バッファを指定バイト数分だけ数値に変換する
#
#	@return		int		数値
#	@param		packet		:	受信パケット(文字列)
#	@param		startIdx	:	解析開始要素index
#	@param		length		:	解析長
#
def convertValueByByte(packet, startIdx, length):
    v = 0

    icnt = 0
    while icnt < length:
        v += packet[startIdx+icnt]*pow(16, icnt)
        icnt += 1

    return v


# 送信コマンドパケットの取得
#		送信コマンドIDと対象センサーモジュールIDのみを引数にしているが、
#		コマンド追加対応の際には、引数の変更/実装変更が必要
#
#	@return			str	パケット文字列
#
#	@param		sendCommandId			:	送信コマンドID
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand(sendCommandId, targetSenssorModuleId):

    measureMode = 0x55

    # コマンドIDに対応したパケットコマンドを返す
    if sendCommandId == DEF_SENDCOMMAND_ID_GETSTATUSINFO:
        return getSendCommand_GetStatusInfo(targetSenssorModuleId)
    elif sendCommandId == DEF_SENDCOMMAND_ID_PREMEASURE:
        return getSendCommand_PreMeasure(targetSenssorModuleId, measureMode,
                                         datetime.datetime.now() + datetime.timedelta(minutes=1))
    elif sendCommandId == DEF_SENDCOMMAND_ID_STARTMEASURE:
        return getSendCommand_StartMeasure(targetSenssorModuleId, measureMode,
                                           datetime.datetime.now() + datetime.timedelta(minutes=1))
    elif sendCommandId == DEF_SENDCOMMAND_ID_ENDMEASURE:
        return getSendCommand_StopMeasure(targetSenssorModuleId)
    # elif sendCommandId == DEF_SENDCOMMAND_ID_SETTIMER:
    #     return getSendCommand_SetTimer(targetSenssorModuleId, hours, minutes, seconds)

    return ""


# コマンドパケットの取得
#		ステータス情報取得
#
#	@return			bytearray	パケットバイト列
#	@param			targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_GetStatusInfo(targetSenssorModuleId):
    packet = bytearray()
    packet.append(0x55)
    packet.append(0x55)
    packet.append(0x05)
    packet += pack('B', gProductId)

    packet += pack('B', targetSenssorModuleId)

    packet += pack('B', DEF_SENDCOMMAND_ID_GETSTATUSINFO)
    # packet.append(0x05)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet.append(0xAA)
    return packet


# コマンドパケットの取得
#		計測準備
#
#	@return			str	パケット文字列
#	@param			targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_PreMeasure(targetSenssorModuleId, measureMode, startTime):
    packet = bytearray()
    packet.append(0x55)
    packet.append(0x55)
    packet.append(0x62)
    packet += pack('B', gProductId)
    # センサID
 #   if isinstance(targetSenssorModuleId, str) == True:
 #       packet += targetSenssorModuleId
 #   else:
 #       packet += struct.pack('B', targetSenssorModuleId)
    packet += pack('B', targetSenssorModuleId)

    # コマンド番号(計測準備:0x1F)
    packet += struct.pack('B', DEF_SENDCOMMAND_ID_PREMEASURE)
    # packet.append(0x1F)
    packet += pack('B', 0x00)  # 予約

    strTime = startTime.strftime('%m%d%H%M')

    # ファイル名
    for i in range(len(strTime)):
        packet += pack('B', 48 + int(strTime[i]))

    packet += struct.pack('B', 0x2e)  # 0x2e .
    packet += struct.pack('B', 0x53)  # 0x53 S
    packet += struct.pack('B', 0x53)  # 0x53 S
    packet += struct.pack('B', 0x62)  # 0x62 b
    packet += struct.pack('B', 0x00)  # 0x00

    packet += struct.pack('B', measureMode)

    for i in range(78):
        # packet += "\x00"  # ファイルコメント、 未使用、予約部分ゼロ埋め(21~99バイト目まで)
        packet.append(0x00)

        # この行はインデントレベルを1つ右にしたので
        # 不具合があれば戻す
        packet += struct.pack('B', checkBCC(packet, 5, len(packet) - 5))
        packet.append(0xAA)
    # print(packet.hex())
    return packet


# コマンドパケットの取得
#		計測開始
#
#	@return			str	パケット文字列
#
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#	@param		measureMode				：	計測モード
#	@param		startTime				：	計測開始時間？	time型
#
def getSendCommand_StartMeasure(targetSenssorModuleId, measureMode, startTime):
    #packet = ""
    #packet += "\x55\x55"
    #packet += pack('B', 11)
    packet = bytearray()
    packet.append(0x55)
    packet.append(0x55)
    packet.append(0x0B)

    packet += struct.pack('B', gProductId)
    packet += struct.pack('B', targetSenssorModuleId)

    packet += struct.pack('B', DEF_SENDCOMMAND_ID_STARTMEASURE)
    # packet.append(0x02)  # コマンド番号、計測開始
    packet += struct.pack('B', startTime.year % 100)  # 下２桁のみを使用
    packet += struct.pack('B', startTime.month)
    packet += struct.pack('B', startTime.day)
    packet += struct.pack('B', startTime.hour)
    packet += struct.pack('B', startTime.minute)

    packet += struct.pack('B', measureMode)
    packet += struct.pack('B', checkBCC(packet, 5, len(packet) - 5))
#    packet += '\xAA'
    packet.append(0xAA)

    return packet


# コマンドパケットの取得
#		計測停止
#	@return			str	パケット文字列
#
#	@param			targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_StopMeasure(targetSenssorModuleId):
    #packet = ""
    #packet += "\x55\x55"
    #packet += pack('B', 5)
    packet = bytearray()
    packet.append(0x55)
    packet.append(0x55)
    packet.append(0x05)
    packet += struct.pack('B', gProductId)
    # if isinstance(targetSenssorModuleId, str) == True:
    #     packet += targetSenssorModuleId
    # else:
    #     packet += struct.pack('B', targetSenssorModuleId)
    packet += struct.pack('B', targetSenssorModuleId)
    packet += struct.pack('B', DEF_SENDCOMMAND_ID_ENDMEASURE)
    packet += struct.pack('B', checkBCC(packet, 5, len(packet) - 5))
#    packet += '\xAA'
    packet.append(0xAA)

    return packet


def clamp(num, min_value, max_value):
    num = max(min(num, max_value), min_value)
    return num

#################TODO######################
# コマンドパケットの取得
#		計測時間設定
#	@return			str	パケット文字列
#
#	@param			targetSenssorModuleId	：	対象センサーモジュールID
#


def getSendCommand_SetTimer(targetSenssorModuleId, hours, minutes, seconds, calibration_time):
    packet = bytearray()
    packet.append(0x55)
    packet.append(0x55)
    packet.append(0x08)
    packet += struct.pack('B', gProductId)

    packet += struct.pack('B', targetSenssorModuleId)
    packet += struct.pack('B', DEF_SENDCOMMAND_ID_SETTIMER)

    hours = clamp(hours, 0, 59)
    minutes = clamp(minutes, 0, 59)
    seconds = clamp(seconds, 0, 59)

    # add time for calibration
    seconds += calibration_time
    if seconds > 59:
        seconds = seconds % 60
        minutes += 1
    if minutes > 59:
        minutes = minutes % 60
        hours += 1

    packet += struct.pack('B', clamp(hours, 0, 59))
    packet += struct.pack('B', clamp(minutes, 0, 59))
    packet += struct.pack('B', clamp(seconds, 0, 59))

    packet += struct.pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet.append(0xAA)

    return packet


# コマンドパケットの取得		(未確認)
#		ファイル情報取得
#
#	@return			str	パケット文字列
#
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_GetFileInformation(targetSenssorModuleId):
    # packet = ""
    # packet += "\x55\x55"
    # packet += pack('B', 5)
    # packet += gProductId  # pack( 'B', gProductId )
    # packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    # packet += pack('B', 7)
    # packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    # packet += "\xaa"

    packet = bytearray()
    packet.append(0x55)
    packet.append(0x55)
    packet.append(0x05)
    packet += struct.pack('B', gProductId)
    packet += struct.pack('B', targetSenssorModuleId)
    packet += pack('B', 7)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
#    packet += '\xAA'
    packet.append(0xAA)

    return packet


# コマンドパケットの取得	(未確認)
#		ファイルデータ取得
#
#	@return			str	パケット文字列
#
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#	@param		fileNo					：	ファイル番号
#	@param		startSequenceNo			：	開始シーケンス番号
#	@param		sequenceNum				：	シーケンス数
#
def getSendCommand_GetFileData(targetSenssorModuleId, fileNo, startSequenceNo, sequenceNum):
    packet = ""
    packet += "\x55\x55"
    packet += pack('B', 15)
    packet += gProductId  # pack( 'B', gProductId )
    packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    packet += pack('B', 9)
    packet += pack('B', fileNo)
    packet += pack('<i', startSequenceNo)
    packet += pack('<i', sequenceNum)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet += "\xaa"

    return packet


# コマンドパケットの取得		(未確認)
#		ファイルコメント取得
#	@return		str:	パケット文字列
#
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#	@param		fileNo					：	ファイル番号
#
def getSendCommand_GetFileComment(targetSenssorModuleId, fileNo):
    packet = ""
    packet += "\x55\x55"
    packet += pack('B', 7)
    packet += gProductId  # pack( 'B', gProductId )
    packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    packet += pack('B', 29)
    packet += pack('B', fileNo * 2 / 8)
    packet += pack('B', fileNo * 2 % 8)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet += "\xaa"

    return packet


# コマンドパケットの取得		(未確認)
#		設定初期化
#	@return			str	パケット文字列
#	@param			targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_ResetSetting(targetSenssorModuleId):
    packet = ""
    packet += "\x55\x55"
    packet += pack('B', 5)
    packet += gProductId  # pack( 'B', gProductId )
    packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    packet += pack('B', 17)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet += "\xaa"

    return packet


# コマンドパケットの取得		(未確認)
#		シリアル番号取得
#
#	@return			str	パケット文字列
#	@param			targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_GetSerialNo(targetSenssorModuleId):
    packet = ""
    packet += "\x55\x55"
    packet += pack('B', 5)
    packet += gProductId  # pack( 'B', gProductId )
    packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    packet += pack('B', 20)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet += "\xaa"

    return packet


# コマンドパケットの取得		(未確認)
#		ファームウェアバージョン取得
#
#	@return		str	パケット文字列
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_GetFirmwareVersionNo(targetSenssorModuleId):
    packet = ""
    packet += "\x55\x55"
    packet += pack('B', 5)
    packet += gProductId  # pack( 'B', gProductId )
    packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    packet += pack('B', 19)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet += "\xaa"

    return packet


# コマンドパケットの取得		(未確認)
#		ハードウェアバージョン取得
#
#	@return		str	パケット文字列
#	@param		targetSenssorModuleId	：	対象センサーモジュールID
#
def getSendCommand_GetFirmwareVersionNo(targetSenssorModuleId):
    packet = ""
    packet += "\x55\x55"
    packet += pack('B', 5)
    packet += gProductId  # pack( 'B', gProductId )
    packet += targetSenssorModuleId  # pack( 'B', targetSenssorModuleId )
    packet += pack('B', 22)
    packet += pack('B', checkBCC(packet, 5, len(packet) - 5))
    packet += "\xaa"

    return packet


# ACKパケットオブジェクト
#
#
class ACKPacket(object):

    # コンストラクタ
    #	@return
    #		なし
    #	@param
    #		なし
    def __init__(self):
        # 残りバイト数
        self.mBytesLen = 0
        # プロダクトID
        self.mProductId = 0
        # ターゲットセンサーモジュールID
        self.mTargetSensorModuleId = 0
        # 応答コード
        self.mResponseCode = 0
        # ACKステータス
        self.mAckStatus = 0
        # BCC
        self.mBcc = 0

    # パケットデータの解析
    #	@return
    #		int	残りバイト数
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def Analyze(self, packet):
        # 2byteはヘッダー分
        self.mBytesLen = packet[2]
        self.mProductId = packet[3]
        self.mTargetSensorModuleId = packet[4]
        self.mResponseCode = packet[5]
        self.mAckStatus = packet[6]
        self.mBcc = packet[7]

        # 1byteはフッター

        return self.mBytesLen

    # コマンドが完了しているか？
    #	@return
    #		boolean		True:正常完了している	False:それ以外
    #	@param
    #		self 		The object pointer.
    def isCommandComplete(self):
        if self.mAckStatus == ord(DEF_ACKSTATUS_CODE_SUCCESS):
            return True
        return False

    # 送信コマンドに　対応したACKパケットか？
    #	@return		True	送信コマンドに対応したACKパケットである
    #				False	それ以外
    #  @param 		self 		The object pointer.
    #				sendCommandId 	送信コマンド
    def isEqualResponseCode(self, sendCommandId):
        cmdId = ord('\x80') + sendCommandId
        print("cmdId:", cmdId, ":", self.mResponseCode)
        if self.mResponseCode == cmdId:
            return True
        return False

    # 情報文字列取得
    #	@return
    #		str		文字列
    #	@param
    #		self 		The object pointer.
    def getString(self):
        result = ""
        result += u"ACK Packet:"
        if self.isCommandComplete() == True:
            result += u"正常"
        else:
            result += u"失敗"
        return result

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        # print("Bytes:" + str(self.mBytesLen))
        # print("mProductId:" + str(self.mProductId))
        # print("mTargetSensorModuleId:" + str(self.mTargetSensorModuleId))
        # print("mResponseCode:" + str(self.mResponseCode))
        # print("mAckStatus:" + str(self.mAckStatus))
        # print("mBcc:" + str(self.mBcc))
        a = 0


# データパケット	共通部分
#		受信データパケットの共通部分管理クラス
#
#
class CDataPacketCommon(object):

    # コンストラクタ
    #	@return
    #		str		なし
    #	@param
    #		self 		The object pointer.
    def __init__(self):
        # 残りバイト数
        self.mBytesLen = 0
        # ターゲットセンサーモジュールID
        self.mTargetSensorModuleId = 0
        # プロダクトID
        self.mProductId = 0
        # 応答コード
        self.mResponseCode = 0
        # BCC
        self.mBcc = 0

    # データパケット先頭部分のみを解析
    #	@return
    #			int		先頭バイト長
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def AnalyzeHeader(self, packet):
        self.mBytesLen = packet[2]
        self.mTargetSensorModuleId = packet[3]
        self.mProductId = packet[4]
        self.mResponseCode = packet[5]
        self.mBcc = packet[self.mBytesLen + 2 - 1]
        return 4

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        # print("BytesLen:" + str(self.mBytesLen))
        # print("mProductId:" + str(self.mProductId))
        # print("mTargetSensorModuleId:" + str(self.mTargetSensorModuleId))
        # print("mResponseCode:" + str(self.mResponseCode))
        # print("mBcc:" + str(self.mBcc))

        a = 0


# ステータス情報取得
#
#
#
class CDataPacket_GetStatusInfo(CDataPacketCommon):

    # コンストラクタ
    #	@return
    #		なし
    #	@param
    #		self 		The object pointer.
    def __init__(self):
        CDataPacketCommon.__init__(self)

        # 計測時間(hour)
        self.mMeasurementHour = 0
        # 計測時間(minute)
        self.mMeasurementMin = 0
        # 計測時間(second)
        self.mMeasurementSec = 0

        # 測定周波数
        self.mMeasuringfrequency = 0
        # 無線チャンネル
        self.mRadioChannel = 0
        # シリアル番号
        self.mSerialNo = 0
        # ハードウェアバージョン
        self.mHardwareVersionNo = 0
        # センサモジュール固有設定
        self.mSensorModuleFixSetting = 0
        # デフォルトキャリブレーションキー
        self.mDefaultCalibrationKey = 0
        # ユーザーキャリブレーションキー
        self.mUserCalibrationKey = 0
        # メモリアドレス
        self.mMemoryAddress = 0
        # メモリ内ファイル数
        self.mMemoryFileCount = 0
        # バッテリ値
        self.mBatteryValue = 0
        # 通信経路（RF[0x00] or UART[0x01])
        self.mTrafficRoute = 0
        # CPU温度
        self.mCpuTemperature = 0

    # パケットを解析
    #	@return
    #			int			残りバイト長
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def Analyze(self, packet):
        icnt = CDataPacketCommon.AnalyzeHeader(self, packet)

        self.mMeasurementHour = packet[7]
        self.mMeasurementMin = packet[8]
        self.mMeasurementSec = packet[9]

        self.mMeasuringfrequency = packet[10] * 16 + packet[11]
        self.mRadioChannel = packet[12]

        self.mSerialNo = packet[13] * pow(16, 4) \
            + packet[14] * pow(16, 3) \
            + packet[15] * pow(16, 2) \
            + packet[16] * pow(16, 1) \
            + packet[17] * pow(16, 0)

        self.mHardwareVersionNo = packet[18] * pow(16, 4) \
            + packet[19] * pow(16, 3) \
            + packet[20] * pow(16, 2) \
            + packet[21] * pow(16, 1) \
            + packet[22] * pow(16, 0)

        self.mMemoryAddress = packet[70] * pow(16, 4) \
            + packet[71] * pow(16, 3) \
            + packet[72] * pow(16, 2) \
            + packet[73] * pow(16, 1)
        self.mMemoryFileCount = packet[74]
        self.mBatteryValue = packet[75]
        self.mTrafficRoute = packet[76]
        self.mCpuTemperature = packet[77]

        return self.mBytesLen

    # 情報文字列取得
    #	@return
    #			str		情報文字列
    #	@param
    #		self 			The object pointer.
    def getResultByString(self):
        resultStr = ""

        resultStr += "ステータス情報取得:結果" + "\n"
        resultStr += "時間:" + str(self.mMeasurementHour) + ":" + str(self.mMeasurementMin) + ":" + str(
            self.mMeasurementSec) + "\n"
        resultStr += "測定周波数:" + str(self.mMeasuringfrequency) + "\n"
        resultStr += "無線チャンネル:" + str(self.mRadioChannel) + "\n"

        return resultStr

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        print("---Command GetStatusInfo---")

        CDataPacketCommon.Print(self)

        print("mMesurementTime:" + str(self.mMeasurementHour) + ":" + str(self.mMeasurementMin) + ":" + str(
            self.mMeasurementSec))

        print("mMeasuringfrequency:" + str(self.mMeasuringfrequency))
        print("mRadioChannel:" + str(self.mRadioChannel))
        print("mSerialNo:" + str(self.mSerialNo))
        print("mHardwareVersionNo:" + str(self.mHardwareVersionNo))
        print("mSensorModuleFixSetting:" + str(self.mSensorModuleFixSetting))
        print("mDefaultCalibrationKey:" + str(self.mDefaultCalibrationKey))
        print("mUserCalibrationKey:" + str(self.mUserCalibrationKey))
        print("mMemoryAddress:" + str(self.mMemoryAddress))
        print("mMemoryFileCount:" + str(self.mMemoryFileCount))
        print("mBatteryValue:" + str(self.mBatteryValue))
        print("mTrafficRoute:" + str(self.mTrafficRoute))
        print("mCpuTemperature:" + str(self.mCpuTemperature))


# 計測開始
#
#
#
class CDataPacket_StartMeasure(CDataPacketCommon):

    # コンストラクタ
    #	@return
    #		なし
    #	@param
    #		self 		The object pointer.
    def __init__(self):
        CDataPacketCommon.__init__(self)

        # バッテリ電圧
        self.mBatteryVoltage = 0
        # シーケンス番号
        self.mSequenceNo = 0

        self.ChannelList1 = []
        self.ChannelList2 = []
        self.ChannelList3 = []
        self.ChannelList4 = []
        self.ChannelList5 = []

    # パケットを解析
    #	@return
    #			int			残りバイト長
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def Analyze(self, packet):
        icnt = CDataPacketCommon.AnalyzeHeader(self, packet)

        # チャンネル	解析処理
        #	@return
        #			[]			数値	リスト
        #	@param
        #		packet			解析対象パケット
        #		startIdx		解析開始Index
        def analyzeChanngle(packet, startIdx):
            li = []
            icnt = 0
            length = 9
            while icnt < length:
                li.append(convertValueByByte(packet, startIdx, 2))
                startIdx += 2
                icnt += 1

            return li

        self.mBatteryVoltage = packet[6]
        self.mSequenceNo = convertValueByByte(packet, 7, 2)
        self.ChannelList1 = analyzeChanngle(packet, 9 + 18 * 0)
        self.ChannelList2 = analyzeChanngle(packet, 9 + 18 * 1)
        self.ChannelList3 = analyzeChanngle(packet, 9 + 18 * 2)
        self.ChannelList4 = analyzeChanngle(packet, 9 + 18 * 3)
        self.ChannelList5 = analyzeChanngle(packet, 9 + 18 * 4)

    # 情報文字列取得
    #	@return
    #			str		情報文字列
    #	@param
    #		self 			The object pointer.
    def getResultByString(self):
        resultStr = ""

        resultStr += "計測開始:結果" + "\n"
        resultStr += "バッテリ電圧:" + str(self.mBatteryVoltage) + "\n"
        resultStr += "シーケンス番号:" + str(self.mSequenceNo) + "\n"

        def getResultChannelList(header, li):
            ret = ""
            if header != None:
                ret += header

            # chId = 1
            # for ch in li:
            #     ret += "<Ch" + str(chId) + ":" + str(ch) + ">"
            #     chId += 1
            return ret

        resultStr += getResultChannelList("--01--\n", self.ChannelList1) + "\n"
        resultStr += getResultChannelList("--02--\n", self.ChannelList2) + "\n"
        resultStr += getResultChannelList("--03--\n", self.ChannelList3) + "\n"
        resultStr += getResultChannelList("--04--\n", self.ChannelList4) + "\n"
        resultStr += getResultChannelList("--05--\n", self.ChannelList5) + "\n"

        return resultStr

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        print("---Command GetStatusInfo---")

        CDataPacketCommon.Print(self)

# 計測開始
#
#
#


class CDataPacket_StartMeasure_X(CDataPacketCommon):

    # コンストラクタ
    #	@return
    #		なし
    #	@param
    #		self 		The object pointer.
    def __init__(self):
        CDataPacketCommon.__init__(self)

        # バッテリ電圧
        self.mBatteryVoltage = 0
        # シーケンス番号
        self.mSequenceNo = 0

        self.ChannelList1 = []
        self.ChannelList2 = []
        self.ChannelList3 = []
        self.ChannelList4 = []
        self.ChannelList5 = []

    # パケットを解析
    #	@return
    #			int			残りバイト長
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def Analyze(self, packet):
        icnt = CDataPacketCommon.AnalyzeHeader(self, packet)

        # チャンネル	解析処理
        #	@return
        #			[]			数値	リスト
        #	@param
        #		packet			解析対象パケット
        #		startIdx		解析開始Index
        def analyzeChanngle(packet, startIdx):
            li = []
            icnt = 0
            length = 9
            while icnt < length:
                li.append(convertValueByByte(packet, startIdx, 2))
                startIdx += 2
                icnt += 1

            return li

        self.mBatteryVoltage = packet[6]
        self.mSequenceNo = convertValueByByte(packet, 7, 2)
        self.ChannelList1 = analyzeChanngle(packet, 9 + 18 * 0)
        self.ChannelList2 = analyzeChanngle(packet, 9 + 18 * 1)
        self.ChannelList3 = analyzeChanngle(packet, 9 + 18 * 2)
        self.ChannelList4 = analyzeChanngle(packet, 9 + 18 * 3)
        self.ChannelList5 = analyzeChanngle(packet, 9 + 18 * 4)

    # 情報文字列取得
    #	@return
    #			str		情報文字列
    #	@param
    #		self 			The object pointer.
    def getResultByString(self):
        resultStr = ""

        resultStr += "計測開始:結果" + "\n"
        resultStr += "バッテリ電圧:" + str(self.mBatteryVoltage) + "\n"
        resultStr += "シーケンス番号:" + str(self.mSequenceNo) + "\n"

        def getResultChannelList(header, li):
            ret = ""
            if header != None:
                ret += header

            # chId = 1
            # for ch in li:
            #     ret += "<Ch" + str(chId) + ":" + str(ch) + ">"
            #     chId += 1
            return ret

        resultStr += getResultChannelList("--01--\n", self.ChannelList1) + "\n"
        resultStr += getResultChannelList("--02--\n", self.ChannelList2) + "\n"
        resultStr += getResultChannelList("--03--\n", self.ChannelList3) + "\n"
        resultStr += getResultChannelList("--04--\n", self.ChannelList4) + "\n"
        resultStr += getResultChannelList("--05--\n", self.ChannelList5) + "\n"

        return resultStr

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        print("---Command GetStatusInfo---")

        CDataPacketCommon.Print(self)


# 計測終了
#		データパケットはないが、オブジェクトだけは用意しておく
#
class CDataPacket_EndMeasure(CDataPacketCommon):

    # コンストラクタ
    #	@return
    #		なし
    #	@param
    #		self 		The object pointer.
    def __init__(self):
        CDataPacketCommon.__init__(self)

    # パケットを解析
    #	@return
    #			int			残りバイト長
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def Analyze(self, packet):
        icnt = CDataPacketCommon.AnalyzeHeader(self, packet)

        return 0

    # 情報文字列取得
    #	@return
    #			str		情報文字列
    #	@param
    #		self 			The object pointer.
    def getResultByString(self):
        return ""

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        print("---Command GetStatusInfo---")

        CDataPacketCommon.Print(self)


# ファイル情報取得
#
#		作成中
#
class CDataPacket_GetFileInformation(CDataPacketCommon):

    # コンストラクタ
    #	@return
    #		なし
    #	@param
    #		self 		The object pointer.
    def __init__(self):
        CDataPacketCommon.__init__(self)

        self.mFileNo = 0
        self.mTotalFileNum = 0
        self.mCalcSamplingFreq = 0
        self.mCalcStartTime = 0
        self.mSamplingNum = 0
        self.mCalcCalibrationKey = 0
        self.mCalcSensorModuleFixSetting = 0

    # パケットを解析
    #	@return
    #			int			残りバイト長
    #	@param
    #		self 			The object pointer.
    #		packet			受信データパケット
    def Analyze(self, packet):
        icnt = CDataPacketCommon.AnalyzeHeader(self, packet)

        self.mFileNo = packet[icnt]
        self.mTotalFileNum = 0
        self.mCalcSamplingFreq = 0
        self.mCalcStartTime = 0
        self.mSamplingNum = 0
        self.mCalcCalibrationKey = 0
        self.mCalcSensorModuleFixSetting = 0

        return self.mBytesLen

    # 情報文字列取得
    #	@return
    #			str		情報文字列
    #	@param
    #		self 			The object pointer.
    def getResultByString(self):
        return ""

    # 確認用コンソール出力
    #	@return
    #			なし
    #	@param
    #		self 			The object pointer.
    def Print(self):
        print("Command GetFileStatus")

        CDataPacketCommon.Print(self)

        print("mFileNo:" + str(self.mFileNo))
        print("mTotalFileNum:" + str(self.mTotalFileNum))
        print("mCalcSamplingFreq:" + str(self.mCalcSamplingFreq))
        print("mCalcStartTime:" + str(self.mCalcStartTime))
        print("mSamplingNum:" + str(self.mSamplingNum))
        print("mCalcCalibrationKey:" + str(self.mCalcCalibrationKey))
        print("mCalcSensorModuleFixSetting:" +
              str(self.mCalcSensorModuleFixSetting))


# ACK/データパケット　ヘッダー共通チェック
#	@return
#		boolean		True　ヘッダーだった	False	ヘッダーではない
#	@param
#		byte1		チェック用バイト
#		byte2		チェック用バイト
def checkHeader(byte1, byte2):
    if byte1 == "0x55" and byte2 == "0x55":
        return True
    return False


# ACK/データパケット　フッター共通チェック
#	@return
#		boolean		True　ヘッダーだった	False	ヘッダーではない
#	@param
#		byte1		チェック用バイト
def checkFooter(byte1):
    if byte1.lower() == "0xaa":
        return True
    return False


# 受信データの解析
#
#	@return			辞書データ
#	@param			packetBufferBytes		:受信パケット
#
def AnalyzePacketThread(packetBufferBytes):
    # パケット長取得
    packetLength = len(packetBufferBytes)
    # print(packetBufferBytes.hex())
    # print("packet len():", packetLength)

    # 返すための辞書を用意
    resultDic = {}

    prevByte = hex(0)

    icnt = 0
    while icnt < packetLength:
        nowByte = hex(packetBufferBytes[icnt])
        # print str(icnt) + ":" + str(nowByte)

        bIsCountStep = True

        # ヘッダをチェック
        if checkHeader(prevByte, nowByte) == True:
            # ACKヘッダ もしくは データヘッダの可能性あり
            # 次のパケットがパケット長定義のはずなので、取得
            byteLength = packetBufferBytes[icnt + 1]

            # フッターをチェック
            footerIndex = icnt + 1 + byteLength
            # パケット長をオーバーしていないかをチェック
            if footerIndex < packetLength:
                if checkFooter(hex(packetBufferBytes[icnt + 1 + byteLength])) == True:

                    # フッターだったので、ACKパケット もしくは データパケット と断定
                    ackPacket = None
                    dataPacket = None

                    # 処理をわかりやすくするため、パケット
                    topIndex = icnt - 1

                    # 応答コードによって、分岐処理
                    responseCode = packetBufferBytes[topIndex + 5]

                    if responseCode == ord('\x80') + DEF_SENDCOMMAND_ID_GETSTATUSINFO:
                        ackPacket = ACKPacket()
                    elif responseCode == ord('\x80') + DEF_SENDCOMMAND_ID_GETSTATUSINFO + 1:
                        dataPacket = CDataPacket_GetStatusInfo()
                    elif responseCode == ord('\x80') + DEF_SENDCOMMAND_ID_PREMEASURE:
                        ackPacket = ACKPacket()
                    elif responseCode == ord('\x80') + DEF_SENDCOMMAND_ID_STARTMEASURE:
                        ackPacket = ACKPacket()
                    elif responseCode == ord('\x80') + DEF_SENDCOMMAND_ID_STARTMEASURE + 1:
                        dataPacket = CDataPacket_StartMeasure()
                    elif responseCode == ord('\x80') + DEF_SENDCOMMAND_ID_ENDMEASURE:
                        ackPacket = ACKPacket()

                    if ackPacket != None:
                        # ACKパケットが有効
                        ackPacket.Analyze(
                            packetBufferBytes[topIndex:topIndex + 2 + byteLength])
                        resultDic['ack'] = ackPacket

                    if dataPacket != None:
                        # データパケットが有効
                        dataPacket.Analyze(
                            packetBufferBytes[topIndex:topIndex + 2 + byteLength])
                        resultDic['dat'] = dataPacket

                    # フッターを設定　＆　解析した分買取を進める
                    prevByte = '0xaa'
                    icnt += (1 + byteLength)

                    # この処理内でバイトを進めたので、デフォルト処理は行わない
                    bIsCountStep = False

        # デフォルト処理
        if bIsCountStep == True:
            #	1byte進める
            prevByte = nowByte
            icnt += 1

    return resultDic
