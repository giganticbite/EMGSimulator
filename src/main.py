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

WHITE = wx.Colour(255, 255, 255)
BLACK = wx.Colour(0, 0, 0)
RED = wx.Colour(255, 0, 0)
BLUE = wx.Colour(0, 0, 255)

class LogText(object):

    #
    #	@return	コンストラクタなし
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


# 身体の向き(自分から見て)


class BodyDirection(Enum):
    LEFT = 0
    RIGHT = 1
    NONE = 2


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
        self.circlecolor_front = RED
        self.circlecolor_back = BLUE

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
        self.emg_datalist.append(subframe.SensorInfo(
            1, 12, 24, subframe.CircleDirection.BACK))

        # # dummy
        # self.emg_datalist.append(subframe.SensorInfo(
        #     2, 12, 24, subframe.CircleDirection.FRONT))
        # 4:内側広筋, 大腿長の1/3
        self.emg_datalist.append(subframe.SensorInfo(
            1, 24, 26, subframe.CircleDirection.FRONT))
        # 2:大腿二頭筋, 大腿長の1/3
        self.emg_datalist.append(subframe.SensorInfo(
            1, 24, 26, subframe.CircleDirection.BACK))
        # 5:前脛骨筋, 下腿長の1/3
        self.emg_datalist.append(subframe.SensorInfo(
            1, 26, 28, subframe.CircleDirection.FRONT))
        # 3:腓腹筋, 下腿長の1/3
        self.emg_datalist.append(subframe.SensorInfo(
            1, 26, 28, subframe.CircleDirection.BACK))

        # self.emg_datalist.append(subframe.SensorInfo(
        #     2, 12, 24, subframe.CircleDirection.BACK))

        # dummy
        self.emg_datalist.append(subframe.SensorInfo(
            2, 12, 24, subframe.CircleDirection.FRONT))

        for i in range(SENSOR_CONNECTION_MAX-6):
            self.emg_datalist.append(subframe.SensorInfo(1, 0, 0, True))

        # ポート番号
        self.StringPortName = "COM3"

        # 計測対象センサー
        self.targetSenssorModuleId = 0xFF  # To all sensors
        # ログ
        self.ListLog = []
        # 使用するセンサーの数
        self.SensorModulenum = 5

    def GetSetTime(self):
        return self.hours, self.minutes, self.seconds

    def GetSetSensorModulenum(self):
        return self.SensorModulenum

    def GetSetCalibrationTime(self):
        return self.calibration_time

    def GetSetColor(self):
        front = (
            self.circlecolor_front[2], self.circlecolor_front[1], self.circlecolor_front[0])
        back = (
            self.circlecolor_back[2], self.circlecolor_back[1], self.circlecolor_back[0])
        return self.circlecolor_front, self.circlecolor_front

    def GetSetRID(self, idx):
        emg_data = self.emg_datalist[idx]
        return emg_data.max_radius_denominator, emg_data.line_startpoint, emg_data.line_endpoint, emg_data.circle_direction


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.emgdata = EMGData()
        # self.pyqtapp_terminate = False
        self.SetWindowStyle()
        self.SerialPort = classSerial.SerialPort()  # シリアルポート    ##	スレッド実行中か？

        self.PlotterOpened = False

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

        self.button_Config = wx.Button(self.panel, wx.ID_ANY, u"設定")
        sizer_2.Add(self.button_Config, 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Prepare = wx.Button(self.panel, wx.ID_ANY, u"計測準備")
        sizer_2.Add(self.button_Prepare, 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Start = wx.Button(self.panel, wx.ID_ANY, u"計測開始")
        sizer_2.Add(self.button_Start, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Stop = wx.Button(self.panel, wx.ID_ANY, u"計測終了")
        sizer_2.Add(self.button_Stop, 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_3, 2, wx.EXPAND, 0)

        self.text_Receive = wx.TextCtrl(
            self.panel, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.text_Receive.SetMinSize((280, 150))
        sizer_3.Add(self.text_Receive, 4, wx.ALL, 4)

        self.receive_checker = []
        sizer_receive_checker = wx.BoxSizer(wx.VERTICAL)
        s_text_riddesc = wx.StaticText(self.panel, wx.ID_ANY, '受信チェック')
        sizer_receive_checker.Add(
            s_text_riddesc, flag=wx.ALIGN_CENTER | wx.TOP)

        idperrow = 17
        for idx in range(0, SENSOR_CONNECTION_MAX, idperrow):
            sizer_rid_2 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_receive_checker.Add(sizer_rid_2, 1, wx.EXPAND)

            for i in range(idperrow):
                self.receive_checker.append(wx.StaticText(
                    self.panel, wx.ID_ANY, label=str(idx+i+1), style=wx.ALIGN_CENTRE_HORIZONTAL))
                self.receive_checker[-1].SetBackgroundColour(WHITE)
                sizer_rid_2.Add(self.receive_checker[-1], 1, wx.EXPAND, 0)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_4, 1, wx.EXPAND, 0)

        sizer_4.Add(sizer_receive_checker, flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_4.Add((100, 20), 2, 0, 0)

        self.button_Plotter = wx.Button(self.panel, wx.ID_ANY, u"グラフ表示")
        sizer_4.Add(self.button_Plotter, 1, wx.ALL, 4)

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
        self.Bind(wx.EVT_BUTTON, self.OnButtonOpenPlotter, self.button_Plotter)

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
        # self.updateMessage()
        self.text_Receive.AppendText(self.emgdata.ListLog[-1]+'\n')

    def updateMessage(self):
        for log in self.emgdata.ListLog:
            self.text_Receive.AppendText(log+'\n')

    def updateReceiveChecker(self, status_sid, color):
        try:
            self.receive_checker[status_sid-1].SetBackgroundColour(color)
            self.Refresh()
        except:
            pass

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

                        # datとackでセンサーIDをあらわすメンバ変数の名前が異なっている
                        # 正しくは4バイト目の「対象センサモジュールID」
                        status_sid = resultDic['dat'].mTargetSensorModuleId
                        if self.emgdata.is_calibration:
                            self.emgdata.emg_datalist[sid-1].emg_data_max = max(
                                self.emgdata.emg_datalist[sid-1].emg_data_max, self.emgdata.emg_datalist[sid-1].emg_data)
                        else:
                            self.emgdata.emg_datalist[sid-1].emg_data_sequence.append(
                                self.emgdata.emg_datalist[sid-1].emg_data)

                        # print(status_sid)
                        try:
                            if not self.receive_checker[status_sid-1].GetBackgroundColour().__eq__(RED):
                                self.updateReceiveChecker(status_sid, RED)
                        except:
                            pass

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
                                        self.updateReceiveChecker(
                                            status_sid, BLUE)
                                    elif status == 0x75:
                                        # self.addLog(
                                        #     str(status_sid)+": 計測準備完了済")
                                        self.updateReceiveChecker(
                                            status_sid, BLUE)
                                    elif status == 0x76:
                                        # self.addLog(
                                        #     str(status_sid)+": 計測準備未完了")
                                        self.updateReceiveChecker(
                                            status_sid, WHITE)
                                elif res_code == 0x82:  # 計測不可時
                                    self.updateReceiveChecker(
                                        status_sid, BLACK)
                                if res_code == 0x84 and status == 0x21:
                                    self.addLog(str(status_sid)+": 通信終了")
                                    self.updateReceiveChecker(
                                        status_sid, WHITE)


                        if 'dat' in resultDic:
                            dat = resultDic['dat']

                    else:
                        dmyCnt += 1

                else:
                    dmyCnt += 1

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
            DEF_SENDCOMMAND_ID_PREMEASURE, self.emgdata.targetSenssorModuleId, self.emgdata.measureMode)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def OnButtonCalibration(self, event):  # 計測開始
        self.emgdata.is_calibration = True
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_STARTMEASURE, self.emgdata.targetSenssorModuleId, self.emgdata.measureMode)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def calibration_timer(self):
        time.sleep(self.emgdata.calibration_time)
        self.emgdata.is_calibration = False
        self.addLog("キャリブレーション終了")

    def OnButtonStart(self, event):  # 計測開始
        self.emgdata.is_calibration = True
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_STARTMEASURE, self.emgdata.targetSenssorModuleId, self.emgdata.measureMode)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)
        self.addLog("キャリブレーション中")
        t = threading.Thread(target=self.calibration_timer)
        t.start()

    def OnButonEnd(self, event):  # 計測終了
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_ENDMEASURE, self.emgdata.targetSenssorModuleId, self.emgdata.measureMode)  # コマンド値, ターゲットID
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

    def OnButtonOpenPlotter(self, event):  # グラフ表示
        self.plotterapp = PyQt5.QtWidgets.QApplication([])
        # self.pyqt_exection
        # plotterapp.exec()

        if not self.PlotterOpened:
            self.PlotterOpened = True

            self.threadpool = QtCore.QThreadPool()
            worker = self.Plotter(self.emgdata)
            self.threadpool.start(worker)

            # t_pyqt = QtCore.QThread()
            # t_pyqt.started.connect(self.pyqt_exection)
            # # t_pyqt.finished.connect(self.plotterapp.exit)
            # # t_pyqt = threading.Thread(target=self.pyqt_exection)
            # t_pyqt.start()

    class Plotter(QtCore.QRunnable):
        def __init__(self, emgdata):
            super().__init__()
            self.emgdata = emgdata

        def run(self):
            print("a")
            self.win = pg.GraphicsLayoutWidget()

            self.win.resize(1000, self.emgdata.SensorModulenum*150)
            print("b")

            # self.win.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            # print("ab")

            self.win.show()
            print("c")

            self.curve_list = []
            # set plot regions
            for i in range(self.emgdata.SensorModulenum):
                title = "real-time plot "+str(i+1)
                p = self.win.addPlot(title=title, col=0, row=i)
                p.setYRange(0, 2)
                p.setXRange(0, 3000)
                self.curve_list.append(p.plot(pen='c'))
            print("d")

            for i, curve in enumerate(self.curve_list):
                curve.getViewBox().enableAutoRange(axis='y', enable=True)
                try:
                    curve.setData(
                        self.emgdata.emg_datalist[i].emg_data_sequence)
                except:
                    pass
            print("e")

            pg.setConfigOptions(antialias=True)
            print("f")

            fps = 120
            timer = QtCore.QTimer()
            timer.timeout.connect(self.plot_emgdata)
            timer.start(int(1/fps * 1000))
            print("g")

            # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            #     PyQt5.QtWidgets.QApplication.instance().exec()

            print("h")
            self.PlotterOpened = False
            self.plotterapp.exec()

        def plot_emgdata(self):
            for i, curve in enumerate(self.curve_list):
                try:
                    curve.setData(
                        self.emgdata.emg_datalist[i].emg_data_sequence)
                except:
                    pass

# end of class MyFrame


class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()

        thread_rs = threading.Thread(target=self.mediapipe_render, daemon=True)
        thread_rs.start()

        return True
    
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

            # render arc
            center = (int((landmark_start_x+landmark_end_x)/2.0),
                      int((landmark_start_y+landmark_end_y)/2.0))
            angle = np.arctan2(landmark_start_y-center[1],
                               landmark_start_x-center[0]) * 180 / np.pi
            radius_max = np.sqrt(
                pow(landmark_start_x-landmark_end_x, 2.0) +
                pow(landmark_start_y-landmark_end_y, 2.0)) / (2*emg_data.max_radius_denominator)

            color = None

            front = (
                self.frame.emgdata.circlecolor_front[2], self.frame.emgdata.circlecolor_front[1], self.frame.emgdata.circlecolor_front[0])
            back = (
                self.frame.emgdata.circlecolor_back[2], self.frame.emgdata.circlecolor_back[1], self.frame.emgdata.circlecolor_back[0])

            if self.frame.emgdata.body_direction == BodyDirection.RIGHT:
                if emg_data.circle_direction == subframe.CircleDirection.FRONT:
                    color = front
                else:
                    color = back
                    angle += 180
            else:
                if emg_data.circle_direction == subframe.CircleDirection.FRONT:
                    color = front
                    angle += 180
                else:
                    color = back

            cv2.ellipse(render_image, center, (int(radius_max*radius_ratio), int(radius_max*radius_ratio)), angle,
                        0, 180, color, thickness=-1)

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

                # if success:
                #     print("sss")

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
