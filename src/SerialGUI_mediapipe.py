from collections import namedtuple
from re import S
import cv2
from enum import Enum
import math

from pyqtgraph.Qt import QtCore
import PyQt5
import pyqtgraph as pg
import sys

import mediapipe as mp
import numpy as np
import schedule
import time

import wx
import threading
import datetime
import classSerial  # ;
import classPacket  # ;
import struct
import subframe

DEF_LOGTEXT_MAX = 10
# コマンドID	定義(必要に応じて追加)
DEF_SENDCOMMAND_ID_GETSTATUSINFO = 5
DEF_SENDCOMMAND_ID_PREMEASURE = 31
DEF_SENDCOMMAND_ID_STARTMEASURE = 2
DEF_SENDCOMMAND_ID_ENDMEASURE = 4

SENSOR_CONNECTION_MAX = 17

# ログ管理用オブジェクト
# ログを貯めておくオブジェクト
# win = pg.GraphicsLayoutWidget()
# win.resize(500, 500)
# win.show()
# p = win.addPlot(title="real-time plot")


class LogText(object):

    # コンストラクタ
    #	@return	なし
    #	@param	self 		The object pointer.
    #	@param	txt 		ログ文字列
    def __init__(self, txt):
        # 発生時間
        self.mDate = datetime.datetime.now()
        # ログ文字列
        self.mText = txt

    # ログ文字列取得
    #	@return	ログ文字列
    #	@param	self 			:The object pointer.
    #	@param	isDisplayTime 	:時間表示をつけるか？
    #							 True:つける　　False:つけない
    def getLog(self, isDisplayTime):
        lineText = ""
        if isDisplayTime == True:
            # 時間を加える
            lineText += str(self.mDate.year) + "/" + \
                str(self.mDate.month) + "/" + str(self.mDate.day)
            lineText += " " + str(self.mDate.hour) + ":" + \
                str(self.mDate.minute) + ":" + str(self.mDate.second)
        lineText += " > " + self.mText
        return lineText



# 半円の向き(筋肉のついている側)


class CircleDirection(Enum):
    FRONT = 0
    BACK = 1

# 身体の向き(自分から見て)


class BodyDirection(Enum):
    LEFT = 0
    RIGHT = 1
    NONE = 2


class SensorInfo:
    def __init__(self, max_radius_denomitor, line_startpoint, line_endpoint, circle_direction):
        self.max_radius_denomitor = max_radius_denomitor

        self.line_startpoint = line_startpoint
        self.line_endpoint = line_endpoint

        self.emg_data_max = 0.0
        self.emg_data = 0.0
        self.emg_data_sequence = []
        self.circle_direction = circle_direction


class EMGData:
    def __init__(self):
        # 計測時間
        self.hours = 0
        self.minutes = 0
        self.seconds = 15

        # 計測モード
        self.measureMode = 0x55

        # (半)円の色
        self.circlecolor_id = subframe.CircleColorID.RED
        self.circlecolor_front = (255, 0, 0)
        self.circlecolor_back = (0, 0, 255)

        # (半)円の半径のスケール
        self.magscale = 5.0

        # キャリブレーション中か？
        self.is_calibration = False
        # キャリブレーション時間
        self.calibration_time = 10

        # 身体の向き
        # self.body_direction = BodyDirection.LEFT
        self.body_direction = BodyDirection.NONE

        # 筋電に関するデータリスト
        self.emg_datalist = []

        # 1:大殿筋, 体幹長の1/2
        # self.emg_datalist.append(SensorInfo(
        #     2, 12, 24, CircleDirection.BACK))

        # # dummy
        # self.emg_datalist.append(SensorInfo(
        #     2, 12, 24, CircleDirection.FRONT))

        # # 2:大腿二頭筋, 大腿長の1/3
        # self.emg_datalist.append(SensorInfo(
        #     3, 24, 26, CircleDirection.BACK))

        # 3:腓腹筋, 下腿長の1/3
        self.emg_datalist.append(SensorInfo(
            1, 26, 28, CircleDirection.BACK))

        # # 4:内側広筋, 大腿長の1/3
        # self.emg_datalist.append(SensorInfo(
        #     3, 24, 26, CircleDirection.FRONT))

        # 5:前脛骨筋, 下腿長の1/3
        self.emg_datalist.append(SensorInfo(
            1, 26, 28, CircleDirection.FRONT))

        for i in range(SENSOR_CONNECTION_MAX-5):
            self.emg_datalist.append(SensorInfo(1, 0, 0, True))

        # ポート番号
        self.StringPortName = "COM3"

        # 計測対象センサー
        self.targetSenssorModuleId = 0xFF  # To all sensors
        # ログ
        self.ListLog = []

    def GetSetTime(self):
        return self.hours, self.minutes, self.seconds
    
    def GetSetColor(self):
        return self.circlecolor_front, self.circlecolor_back


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.emgdata = EMGData()
        # self.pyqtapp_terminate = False
        self.SetWindowStyle()
        self.SerialPort = classSerial.SerialPort()  # シリアルポート    ##	スレッド実行中か？

    def SetWindowStyle(self):
        # self.SetSize((700, 450))
        self.SetSize((500, 300))
        self.SetTitle(u"動作シミュレーター")

        self.panel = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)

        self.combo_box_Serialport = wx.ComboBox(self.panel, wx.ID_ANY, choices=[
                                                "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7"], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        sizer_2.Add(self.combo_box_Serialport, 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Connect = wx.Button(self.panel, wx.ID_ANY, u"接続")
        sizer_2.Add(self.button_Connect, 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Prepare = wx.Button(self.panel, wx.ID_ANY, u"計測準備")
        sizer_2.Add(self.button_Prepare, 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        # self.button_Calibration = wx.Button(
        #     self.panel, wx.ID_ANY, u"キャリブレーション")
        # sizer_2.Add(self.button_Calibration, 0,
        #             wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Start = wx.Button(self.panel, wx.ID_ANY, u"計測開始")
        sizer_2.Add(self.button_Start, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_3, 2, wx.EXPAND, 0)

        self.text_Receive = wx.TextCtrl(
            self.panel, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.text_Receive.SetMinSize((320, 150))
        sizer_3.Add(self.text_Receive, 4, wx.ALL | wx.EXPAND, 4)

        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_5, 1, wx.EXPAND, 0)

        self.text_Emg = wx.TextCtrl(self.panel, wx.ID_ANY, "")
        sizer_5.Add(self.text_Emg, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_4, 1, wx.EXPAND, 0)

        sizer_4.Add((150, 20), 2, 0, 0)

        self.button_Config = wx.Button(self.panel, wx.ID_ANY, u"設定")
        sizer_4.Add(self.button_Config, 1, wx.ALL, 4)

        self.button_Stop = wx.Button(self.panel, wx.ID_ANY, u"計測終了")
        sizer_4.Add(self.button_Stop, 1, wx.ALL, 4)

        self.button_Exit = wx.Button(self.panel, wx.ID_ANY, u"終了")
        sizer_4.Add(self.button_Exit, 1, wx.ALL, 4)

        self.panel.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.OnButtonConnect, self.button_Connect)
        self.Bind(wx.EVT_BUTTON, self.OnButtonPrepare, self.button_Prepare)
        # self.Bind(wx.EVT_BUTTON, self.OnButtonCalibration,
        #           self.button_Calibration)
        self.Bind(wx.EVT_BUTTON, self.OnButtonStart, self.button_Start)
        self.Bind(wx.EVT_BUTTON, self.OnButonEnd, self.button_Stop)
        self.Bind(wx.EVT_BUTTON, self.OnButtonExit, self.button_Exit)
        self.Bind(wx.EVT_BUTTON, self.OnButtonConfig, self.button_Config)

        self.Bind(wx.EVT_CLOSE, self.ExitHandler)
        self.Show(True)

    def OnButtonConfig(self, event):
        subframe.SubFrame(self.SerialPort, self.emgdata)

    def OnPaint(self, event):
        dc = wx.PaintDC(self.panel_1)
        dc.SetPen(wx.Pen('blue'))
        dc.SetBrush(wx.Brush('blue'))

    #	True:実行中		False:それ以外
    mbIsRunningThread = False

    # スレッドの終了待ち中か？
    #	True:処理終了待ち中		False:それ以外
    mbIsWaitThread = False

    def stopThreadReceive(self):
        if self.mbIsRunningThread == True:
            # スレッドが走っている状態であれば、終了待ちを行う
            self.mbIsWaitThread = True
            self.mbIsRunningThread = False
            self.th = None

    def startThreadReceive(self):
        # 起動中のスレッド停止
        self.stopThreadReceive()
        self.mbIsRunningThread = True
        # self.main_thread = threading.current_thread()
        self.th = threading.Thread(
            target=self.ReceivePacketASync, name="thr1", args=())
        self.th.setDaemon(True)
        self.th.start()

    # ログを追加
    #    @return        なし
    #
    #    @param        self         :    The object pointer.
    #    @param        logString    :    追加するログ文字列
    def addLog(self, logString):
        # 一定数以上を超えないように、古いログから削除
        if DEF_LOGTEXT_MAX < len(self.emgdata.ListLog):
            del self.emgdata.ListLog[0]

        # ログを追加
        # newLog = LogText(logString)
        # self.emgdata.ListLog.append(newLog)
        self.emgdata.ListLog.append(logString)
        # ログを更新
        self.updateMessage()

    def updateMessage(self):
        for log in self.emgdata.ListLog:
            self.text_Receive.AppendText(log+'\n')

    # パケットの受信待ち    スレッド処理
    #        スレッドから呼び出される
    #    @return        なし
    #    @param        self :    The object pointer.

    def ReceivePacketASync(self):
        self.addLog(u"データ受信待ちスレッド開始")

        # else分岐処理を残しておきたいための変数
        dmyCnt = 0

        # 受信データ取得
        while self.mbIsRunningThread == True:
            if self.SerialPort.isEnableAccess() == True:
                packetBuff = self.SerialPort.receiveBufferASync()

                if isinstance(packetBuff, bytes) and packetBuff != 0:

                    # 受信データ解析
                    resultDic = classPacket.AnalyzePacketThread(packetBuff)

                    # classPacket.AnalyzePacketThread(packetBuff)の中で受信パケットの解析を行っているので
                    # 返り値を見る方がパケットにエラーがあった時でも正しく扱えると予想される
                    # 今回使用しているのはDSPワイヤレス筋電センサ(乾式)なので、パケットはType F

                    # resultDic.keys() => 'ack', 'dat'
                    if resultDic.get('dat') != None:
                        sid = struct.unpack_from(
                            b'>b', packetBuff, 3)[0]

                        self.emgdata.emg_datalist[sid-1].emg_data = round(struct.unpack_from(
                            b'>f', packetBuff, 15)[0], 2)

                        if self.emgdata.is_calibration:
                            self.emgdata.emg_datalist[sid-1].emg_data_max = max(
                                self.emgdata.emg_datalist[sid-1].emg_data_max, self.emgdata.emg_datalist[sid-1].emg_data)
                        else:
                            self.emgdata.emg_datalist[sid-1].emg_data_sequence.append(
                                self.emgdata.emg_datalist[sid-1].emg_data)

                    if 0 < len(resultDic):
                        # self.addLog(u"受信成功")
                        if 'ack' in resultDic:
                            ack = resultDic['ack']
                            if ack != None:
                                status_sid = ack.mProductId
                                res_code = ack.mResponseCode
                                status = ack.mAckStatus

                                if res_code == 0x9F:
                                    if status == 0x21:
                                        self.addLog(str(status_sid)+": 計測準備完了")
                                    elif status == 0x75:
                                        self.addLog(
                                            str(status_sid)+": 計測準備完了済")
                                    elif status == 0x76:
                                        self.addLog(
                                            str(status_sid)+": 計測準備未完了")
                                if res_code == 0x84 and status == 0x21:
                                    self.addLog(str(status_sid)+": 通信終了")

                                self.addLog(ack.getString())

                        if 'dat' in resultDic:
                            dat = resultDic['dat']
                            # if dat != None:
                            #     self.addLog(dat.getResultByString())

                    else:
                        # self.addLog(u"受信失敗")
                        dmyCnt += 1

                else:
                    dmyCnt += 1
                    # print "running ReceivePacketASync..."

            else:
                # ポートが無効なので、いったん停止
                time.sleep(2)
                print("running ReceivePacketASync")

        print("finish ReceivePacketASync")
        self.addLog(u"データ受信待ちスレッド終了")
        self.mbIsWaitThread = False

    def OnButtonConnect(self, event):  # 接続
        bIsOpen = True
        if self.SerialPort.isEnableAccess() == True:
            # すでに、PortOpen済みなので閉じる処理を行う
            bIsOpen = False
        else:
            # ポートが無効なので、開く処理
            bIsOpen = True

        if bIsOpen == True:
            # ポート開く処理を開始
            # self.SerialPort.portOpen(self.EntryPortName.get())
            self.emgdata.StringPortName = self.combo_box_Serialport.GetValue()
            print("portPath:", self.emgdata.StringPortName)
            self.SerialPort.portOpen(self.emgdata.StringPortName)
            if self.SerialPort.isEnableAccess() == True:
                # アクセス開始できたので、受信スレッド開始
                self.startThreadReceive()
                self.button_Connect.SetLabel("切断")
            else:
                # portが開けなかった
                wx.MessageBox(u"portが開けませんでした\nポートのパス:" +
                              self.emgdata.StringPortName, u"ポートエラー", style=wx.OK)
        else:
            # ポート閉じる処理を開始
            self.stopThreadReceive()
            self.addLog("Port Close:" + self.SerialPort.mDeviceName)
            self.button_Connect.SetLabel("接続")

    def OnButtonPrepare(self, event):  # 計測準備
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_PREMEASURE, self.emgdata.targetSenssorModuleId)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def OnButtonCalibration(self, event):  # 計測開始
        self.emgdata.is_calibration = True
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_STARTMEASURE, self.emgdata.targetSenssorModuleId)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def calibration_timer(self):
        time.sleep(10)
        self.emgdata.is_calibration = False
        self.addLog("キャリブレーション終了")

    def OnButtonStart(self, event):  # 計測開始
        self.emgdata.is_calibration = True
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_STARTMEASURE, self.emgdata.targetSenssorModuleId)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)
        self.addLog("キャリブレーション中")
        t = threading.Thread(target=self.calibration_timer)
        t.start()

    def OnButonEnd(self, event):  # 計測終了
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_ENDMEASURE, self.emgdata.targetSenssorModuleId)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def OnButtonExit(self, event):  # プログラム終了

        if self.SerialPort.isEnableAccess() == True:
            self.stopThreadReceive()
            self.addLog("Port Close:" + self.SerialPort.mDeviceName)
            self.button_Connect.SetLabel("接続")

        # self.pyqtapp_terminate = True
        PyQt5.QtWidgets.QApplication.quit()

        # exit()を使うと、次に実行したときにポートに接続できなくなる不具合がある
        # (この不具合はsports sensingのSDKによるもの)
        # 正常終了するためにはwx.Frame自体をDestroyする必要がある
        # (参考：SDKのpythonサンプルプログラム内, classGui.pyのpushButtonDestory())
        self.Destroy()

    def ExitHandler(self, event):
        self.Destroy()


# end of class MyFrame

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()

        thread_rs = threading.Thread(target=self.mediapipe_render, daemon=True)
        thread_rs.start()

        t_pyqt = threading.Thread(target=self.pyqt_exection)
        t_pyqt.start()

        # self.pyqt_exection()

        return True

    def pyqt_exection(self):
        self.win = pg.GraphicsLayoutWidget()
        self.win.resize(1000, 600)
        self.win.show()

        self.curve_list = []
        # set plot regions
        for i in range(3):
            title = "real-time plot "+str(i+1)
            p = self.win.addPlot(title=title, col=0, row=i)
            p.setYRange(0, 2)
            p.setXRange(0, 3000)
            self.curve_list.append(p.plot(pen='c'))

        for i, curve in enumerate(self.curve_list):
            curve.getViewBox().enableAutoRange(axis='y', enable=True)
            try:
                curve.setData(
                    self.frame.emgdata.emg_datalist[i].emg_data_sequence)
            except:
                pass

        pg.setConfigOptions(antialias=True)

        fps = 120
        timer = QtCore.QTimer()
        timer.timeout.connect(self.plot_emgdata)
        timer.start(int(1/fps * 1000))

        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            PyQt5.QtWidgets.QApplication.instance().exec_()

    def plot_emgdata(self):
        for i, curve in enumerate(self.curve_list):
            try:
                curve.setData(
                    self.frame.emgdata.emg_datalist[i].emg_data_sequence)
            except:
                pass

    def render_ids_3d(self, render_image, poselandmarks, data_list_past):
        log_r = np.math.log(
            abs(self.frame.emgdata.emg_datalist[0].emg_data)+1.0, 1.1)
        mag = 5.0

        # calculate 3D keypoints and display them
        for i, emg_data_past in enumerate(data_list_past):
            radius_ratio = 0

            emg_data = self.frame.emgdata.emg_datalist[i]

            # TODO:最大径に対する比率に直す
            if emg_data.emg_data_max != 0:
                radius_ratio = emg_data_past/emg_data.emg_data_max


            if poselandmarks == None:
                return

            landmark_start_x = render_image.shape[1] * \
                poselandmarks.landmark[emg_data.line_startpoint].x
            landmark_start_y = render_image.shape[0] * \
                poselandmarks.landmark[emg_data.line_startpoint].y
            landmark_end_x = render_image.shape[1] * \
                poselandmarks.landmark[emg_data.line_endpoint].x
            landmark_end_y = render_image.shape[0] * \
                poselandmarks.landmark[emg_data.line_endpoint].y

            if (landmark_start_x == None or landmark_start_y == None or
                    landmark_end_x == None or landmark_end_y == None):
                continue

            # render_image = cv2.circle(render_image,
            #                           (int(landmark_start.x*render_image.shape[1]),
            #                            int(landmark_start.y*render_image.shape[0])),
            #                           10, (0, 0, 255), -1)

            # render arc
            center = (int((landmark_start_x+landmark_end_x)/2.0),
                      int((landmark_start_y+landmark_end_y)/2.0))
            angle = np.arctan2(landmark_start_y-center[1],
                               landmark_start_x-center[0]) * 180 / np.pi
            radius_max = np.sqrt(
                pow(landmark_start_x-landmark_end_x, 2.0) +
                pow(landmark_start_y-landmark_end_y, 2.0)) / (2*emg_data.max_radius_denomitor)

            if emg_data.circle_direction == CircleDirection.BACK:
                angle += 180
            color = None

            if self.frame.emgdata.body_direction == BodyDirection.RIGHT:
                if emg_data.circle_direction == CircleDirection.FRONT:
                    color = self.frame.emgdata.circlecolor_back
                else:
                    color = self.frame.emgdata.circlecolor_front
            else:
                if emg_data.circle_direction == CircleDirection.FRONT:
                    color = self.frame.emgdata.circlecolor_back
                else:
                    color = self.frame.emgdata.circlecolor_front

            cv2.ellipse(render_image, center, (int(radius_max*radius_ratio), int(radius_max*radius_ratio)), angle,
                        0, 180, color, thickness=-1)
        # for emg_data in self.frame.emgdata.emg_datalist:
        #     radius_ratio = 0

        #     # TODO:最大径に対する比率に直す
        #     if emg_data.emg_data_max != 0:
        #         if self.frame.emgdata.radiusscale == RadiusScale.LOGARITHMIC:
        #             radius_ratio = emg_data.emg_data/emg_data.emg_data_max
        #         else:
        #             radius_ratio = emg_data.emg_data/emg_data.emg_data_max

        #     if poselandmarks == None:
        #         return

        #     landmark_start_x = render_image.shape[1] * \
        #         poselandmarks.landmark[emg_data.line_startpoint].x
        #     landmark_start_y = render_image.shape[0] * \
        #         poselandmarks.landmark[emg_data.line_startpoint].y
        #     landmark_end_x = render_image.shape[1] * \
        #         poselandmarks.landmark[emg_data.line_endpoint].x
        #     landmark_end_y = render_image.shape[0] * \
        #         poselandmarks.landmark[emg_data.line_endpoint].y

        #     if (landmark_start_x == None or landmark_start_y == None or
        #             landmark_end_x == None or landmark_end_y == None):
        #         continue

        #     # render_image = cv2.circle(render_image,
        #     #                           (int(landmark_start.x*render_image.shape[1]),
        #     #                            int(landmark_start.y*render_image.shape[0])),
        #     #                           10, (0, 0, 255), -1)

        #     # render arc
        #     center = (int((landmark_start_x+landmark_end_x)/2.0),
        #               int((landmark_start_y+landmark_end_y)/2.0))
        #     angle = np.arctan2(landmark_start_y-center[1],
        #                        landmark_start_x-center[0]) * 180 / np.pi
        #     radius_max = np.sqrt(
        #         pow(landmark_start_x-landmark_end_x, 2.0) +
        #         pow(landmark_start_y-landmark_end_y, 2.0)) / (2*emg_data.max_radius_denomitor)

        #     if emg_data.circle_direction == CircleDirection.BACK:
        #         angle += 180
        #     color = None

        #     if self.frame.emgdata.body_direction == BodyDirection.RIGHT:
        #         if emg_data.circle_direction == CircleDirection.FRONT:
        #             color = self.frame.emgdata.circlecolor_back
        #         else:
        #             color = self.frame.emgdata.circlecolor_front
        #     else:
        #         if emg_data.circle_direction == CircleDirection.FRONT:
        #             color = self.frame.emgdata.circlecolor_back
        #         else:
        #             color = self.frame.emgdata.circlecolor_front

        #     cv2.ellipse(render_image, center, (int(radius_max*radius_ratio), int(radius_max*radius_ratio)), angle,
        #                 0, 180, color, thickness=-1)

    def mediapipe_render(self):

        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_pose = mp.solutions.pose

        cap = cv2.VideoCapture(0)

        with mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as pose:
            while cap.isOpened():
                success, image = cap.read()

                data_list_past = []
                for data in self.frame.emgdata.emg_datalist:
                    data_list_past.append(data.emg_data)

                if not success:
                    print("Ignoring empty camera frame.")
                    # If loading a video, use 'break' instead of 'continue'.
                    continue

                # To improve performance, optionally mark the image as not writeable to
                # pass by reference.
                image.flags.writeable = False
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose.process(image)

                # Draw the pose annotation on the image.
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

                # image = cv2.circle(image,
                #                    (int(results.pose_landmarks.landmark[0].x*image.shape[1]),
                #                     int(results.pose_landmarks.landmark[0].y*image.shape[0])),
                #                    10, (0, 0, 255), -1)

                self.render_ids_3d(
                    image, results.pose_landmarks, data_list_past
                )
                # Flip the image horizontally for a selfie-view display.
                cv2.imshow('MediaPipe Pose', image)
                # cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
                if cv2.waitKey(5) & 0xFF == 27:
                    break
        cap.release()


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
