from collections import namedtuple
import cv2
from enum import Enum
import math
import numpy as np
import os
import pyrealsense2 as rs
from skeletontracker import skeletontracker
import time
import util as cm

import wx
import threading
import datetime
import classSerial  # ;
import classPacket  # ;
import struct
DEF_LOGTEXT_MAX = 32
# コマンドID	定義(必要に応じて追加)
DEF_SENDCOMMAND_ID_GETSTATUSINFO = 5
DEF_SENDCOMMAND_ID_PREMEASURE = 31
DEF_SENDCOMMAND_ID_STARTMEASURE = 2
DEF_SENDCOMMAND_ID_ENDMEASURE = 4

# ログ管理用オブジェクト
# ログを貯めておくオブジェクト


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


class CircleColorID(Enum):
    RED = 0
    BLACK = 1
    BLUE = 2


class RadiusScale(Enum):
    LOGARITHMIC = 0
    LINEAR = 1


class EMGData:
    def __init__(self):
        self.hours = 0
        self.minutes = 0
        self.seconds = 15

        self.measureMode = 0x55

        self.circlecolor_id = CircleColorID.RED
        self.circlecolor = (0, 0, 255)

        self.radiusscale = RadiusScale.LOGARITHMIC
        self.magscale = 5.0

        self.emg_data = 0.0
        self.StringPortName = "COM3"
        # モジュールID
        self.targetSenssorModuleId = 3
        self.ListLog = []

    def GetSetTime(self):
        return self.hours, self.minutes, self.seconds


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.emgdata = EMGData()

        self.SetWindowStyle()
        self.SerialPort = classSerial.SerialPort()  # シリアルポート    ##	スレッド実行中か？

    def SetWindowStyle(self):
        # self.SetSize((700, 450))
        self.SetSize((450, 300))
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
        self.Bind(wx.EVT_BUTTON, self.OnButtonStart, self.button_Start)
        self.Bind(wx.EVT_BUTTON, self.OnButonEnd, self.button_Stop)
        self.Bind(wx.EVT_BUTTON, self.OnButtonExit, self.button_Exit)
        self.Bind(wx.EVT_BUTTON, self.OnButtonConfig, self.button_Config)

        self.Bind(wx.EVT_CLOSE, self.ExitHandler)
        self.Show(True)

    def OnButtonConfig(self, event):
        SubFrame(self.SerialPort, self.emgdata)

    def OnPaint(self, event):
        dc = wx.PaintDC(self.panel_1)
        dc.SetPen(wx.Pen('blue'))
        dc.SetBrush(wx.Brush('blue'))
        # dc.DrawRectangle(0, 0, int(self.emgdata.emg_data*20+100), 20)

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

        idx = 0

        # 受信データ取得
        while self.mbIsRunningThread == True:
            if self.SerialPort.isEnableAccess() == True:
                packetBuff = self.SerialPort.receiveBufferASync()
##############################################################################
# 元コードではpacketbuffがstrかつその長さが0以上であるときにtrue
# ポート開設後、スレッドが走っている間はデータを受信するので、計測準備中もここを通る

                # # 計測中かつデータパケットならば
                # if packetBuff != 0 and packetBuff.hex()[10] == "8" and packetBuff.hex()[11] == "3":
                #     emgdata.emg_data = round(struct.unpack_from(
                #         b'>f', packetBuff, 11)[0], 2)
                #     # print(str(emgdata.emg_data))

                #     self.text_Emg.Clear()  # 筋電データクリア
                #     self.text_Emg.AppendText(str(emgdata.emg_data))  # 新しいデータをappend

                #     # dc = dc = wx.PaintDC(self.panel_1)
                #     dc = wx.PaintDC(self.panel_1)
                #     dc.SetPen(wx.Pen('blue'))
                #     dc.SetBrush(wx.Brush('blue'))
                #     dc.DrawRectangle(0, 0, int(emgdata.emg_data*20+100), 20)

                #     self.addLog("\n")
##############################################################################

                # if packetBuff != 0:
                #     print(packetBuff)
                #     print(type(packetBuff))

                # if packetBuff != 0:
                if isinstance(packetBuff, bytes) and packetBuff != 0:
                    # print "受信:",packetBuff

                    # 受信データ解析
                    resultDic = classPacket.AnalyzePacketThread(packetBuff)
                    # print "Result:",resultDic

                    # classPacket.AnalyzePacketThread(packetBuff)の中で受信パケットの解析を行っているので
                    # 返り値を見る方がパケットにエラーがあった時でも正しく扱えると予想される
                    # 今回使用しているのはDSPワイヤレス筋電センサ(乾式)なので、パケットはType F

                    # resultDic.keys() => 'ack', 'dat'
                    if resultDic.get('dat') != None:
                        self.emgdata.emg_data = round(struct.unpack_from(
                            b'>f', packetBuff, 15)[0], 2)

                        # self.emgdata.emg_data = round(struct.unpack_from(
                        #     b'>f', packetBuff, 11)[0], 2)

                        idx += 1
                        # self.addLog("\n")

                        # dc = dc = wx.PaintDC(self.panel_1)
                        # dc = wx.PaintDC(self.panel_1)
                        # dc.SetPen(wx.Pen('blue'))
                        # dc.SetBrush(wx.Brush('blue'))
                        # dc.DrawRectangle(0, 0, int(emgdata.emg_data*20+100), 20)

                    if 0 < len(resultDic):
                        # self.addLog(u"受信成功")
                        if 'ack' in resultDic:
                            ack = resultDic['ack']
                            if ack != None:
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

        self.text_Emg.Clear()  # 筋電データクリア
        self.text_Emg.AppendText(
            str(idx)+": "+str(self.emgdata.emg_data))  # 新しいデータをappend
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

    def OnButtonStart(self, event):  # 計測開始
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_STARTMEASURE, self.emgdata.targetSenssorModuleId)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def OnButonEnd(self, event):  # 計測終了
        sendCommandBuff = classPacket.getSendCommand(
            DEF_SENDCOMMAND_ID_ENDMEASURE, self.emgdata.targetSenssorModuleId)  # コマンド値, ターゲットID
        self.SerialPort.sendPacket(sendCommandBuff)

    def OnButtonExit(self, event):  # プログラム終了

        if self.SerialPort.isEnableAccess() == True:
            self.stopThreadReceive()
            self.addLog("Port Close:" + self.SerialPort.mDeviceName)
            self.button_Connect.SetLabel("接続")

        # exit()を使うと、次に実行したときにポートに接続できなくなる不具合がある
        # (この不具合はsports sensingのSDKによるもの)
        # 正常終了するためにはwx.Frame自体をDestroyする必要がある
        # (参考：SDKのpythonサンプルプログラム内, classGui.pyのpushButtonDestory())
        self.Destroy()

        # exit()

    def ExitHandler(self, event):
        self.Destroy()


# end of class MyFrame

# Config Window
class SubFrame(wx.Dialog):
    def __init__(self, SerialPort, emgdata):
        # MyFrame().__init__(self)
        self.SerialPort = SerialPort
        self.emgdata = emgdata

        wx.Dialog.__init__(self, None, -1, "設定")
        self.SetSize((750, 250))

        self.SetWindowStyle()
        self.Bind(wx.EVT_CLOSE, self.ExitHandler)

        self.Show(True)
        # self.ShowModal()

    ##############################
    # Component Tree
    # Whole
    #   > Upper
    #     > Upper Left
    #       > description
    #       > Timer
    #         > hh
    #         > mm
    #         > ss
    #     > Upper Right
    #       > description
    #       > radio buttons
    #   > Lower
    #     > Lower Left
    #       > description
    #       > radio buttons
    #     > Lower Right
    #       > description
    #       > Circle Sizer
    #         > Radius scale
    #         > Magnification scale
    ##############################

    def SetWindowStyle(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        sizer_whole = wx.BoxSizer(wx.VERTICAL)

        sizer_upper = wx.BoxSizer(wx.HORIZONTAL)
        sizer_lower = wx.BoxSizer(wx.HORIZONTAL)
        sizer_whole.Add(sizer_upper, 1, wx.EXPAND, 0)
        sizer_whole.Add(sizer_lower, 1, wx.EXPAND, 0)

        #############################
        # Timer setting (upper left)
        #############################
        sizer_ul = wx.BoxSizer(wx.VERTICAL)
        sizer_upper.Add(sizer_ul, 1, wx.EXPAND, 0)
        s_text_timerdesc = wx.StaticText(self.panel, wx.ID_ANY, '計測時間設定')
        sizer_ul.Add(s_text_timerdesc, flag=wx.ALIGN_CENTER | wx.TOP)

        sizer_timer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_ul.Add(sizer_timer, 1, wx.EXPAND, 0)

        sizer_hh = wx.BoxSizer(wx.VERTICAL)
        sizer_mm = wx.BoxSizer(wx.VERTICAL)
        sizer_ss = wx.BoxSizer(wx.VERTICAL)

        sizer_timer.Add(sizer_hh, 1, wx.EXPAND, 0)
        sizer_timer.Add(sizer_mm, 1, wx.EXPAND, 0)
        sizer_timer.Add(sizer_ss, 1, wx.EXPAND, 0)

        # get times set before or default
        hours, minutes, seconds = self.emgdata.GetSetTime()

        s_text_hh = wx.StaticText(self.panel, wx.ID_ANY, 'hh(0-59)')
        self.spinctrl_h = wx.SpinCtrl(
            self.panel, wx.ID_ANY, value=str(hours), max=59)
        sizer_hh.Add(s_text_hh, flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_hh.Add(self.spinctrl_h, flag=wx.ALIGN_CENTER | wx.TOP)

        s_text_mm = wx.StaticText(self.panel, wx.ID_ANY, 'mm(0-59)')
        self.spinctrl_m = wx.SpinCtrl(
            self.panel, wx.ID_ANY, value=str(minutes), max=59)
        sizer_mm.Add(s_text_mm, flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_mm.Add(self.spinctrl_m, flag=wx.ALIGN_CENTER | wx.TOP)

        s_text_ss = wx.StaticText(self.panel, wx.ID_ANY, 'ss(0-59)')
        self.spinctrl_s = wx.SpinCtrl(
            self.panel, wx.ID_ANY, value=str(seconds), max=59)
        sizer_ss.Add(s_text_ss, flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_ss.Add(self.spinctrl_s, flag=wx.ALIGN_CENTER | wx.TOP)

        #############################
        # Connetion mode (upper right)
        #############################
        sizer_ur = wx.BoxSizer(wx.VERTICAL)
        sizer_upper.Add(sizer_ur, 1, wx.EXPAND, 0)
        s_text_modedesc = wx.StaticText(
            self.panel, wx.ID_ANY, '計測モード設定(同時使用可能ID)')
        sizer_ur.Add(s_text_modedesc, flag=wx.ALIGN_CENTER | wx.TOP)

        sizer_connection_mode = wx.BoxSizer(wx.HORIZONTAL)
        sizer_ur.Add(sizer_connection_mode,
                     flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.RB_40hz = wx.RadioButton(
            self.panel, wx.ID_ANY, '40Hz(1-3)', style=wx.RB_GROUP)
        self.RB_20hz = wx.RadioButton(self.panel, wx.ID_ANY, '20Hz(1-7)')
        self.RB_10hz = wx.RadioButton(self.panel, wx.ID_ANY, '10Hz(1-15)')

        if self.emgdata.measureMode == 0x55:
            self.RB_40hz.SetValue(True)
        elif self.emgdata.measureMode == 0x45:
            self.RB_20hz.SetValue(True)
        elif self.emgdata.measureMode == 0x35:
            self.RB_10hz.SetValue(True)
        else:
            self.RB_40hz.SetValue(True)

        sizer_connection_mode.Add(self.RB_40hz, 1, wx.EXPAND, 0)
        sizer_connection_mode.Add(self.RB_20hz, 1, wx.EXPAND, 0)
        sizer_connection_mode.Add(self.RB_10hz, 1, wx.EXPAND, 0)

        #############################
        # Circle color (lower left)
        #############################
        sizer_ll = wx.BoxSizer(wx.VERTICAL)
        sizer_lower.Add(sizer_ll, 1, wx.EXPAND, 0)
        s_text_ccdesc = wx.StaticText(
            self.panel, wx.ID_ANY, '円の色')
        sizer_ll.Add(s_text_ccdesc, flag=wx.ALIGN_CENTER | wx.TOP)

        sizer_circle_color = wx.BoxSizer(wx.HORIZONTAL)
        sizer_ll.Add(sizer_circle_color,
                     flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        self.RB_RED = wx.RadioButton(
            self.panel, wx.ID_ANY, '赤', style=wx.RB_GROUP)
        self.RB_BLACK = wx.RadioButton(self.panel, wx.ID_ANY, '黒')

        if self.emgdata.circlecolor_id == CircleColorID.RED:
            self.RB_RED.SetValue(True)
        elif self.emgdata.circlecolor_id == CircleColorID.BLACK:
            self.RB_BLACK.SetValue(True)
        else:
            self.RB_RED.SetValue(True)

        sizer_circle_color.Add(self.RB_RED, 1, wx.EXPAND, 0)
        sizer_circle_color.Add(self.RB_BLACK, 1, wx.EXPAND, 0)

        #############################
        # Circle size (lower right)
        #############################
        sizer_lr = wx.BoxSizer(wx.VERTICAL)
        sizer_lower.Add(sizer_lr, 1, wx.EXPAND, 0)
        s_text_csdesc = wx.StaticText(
            self.panel, wx.ID_ANY, '円のサイズ')
        sizer_lr.Add(s_text_csdesc, flag=wx.ALIGN_CENTER | wx.TOP)

        sizer_circle_size = wx.BoxSizer(wx.HORIZONTAL)
        sizer_lr.Add(sizer_circle_size,
                     flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        sizer_radius_scale = wx.BoxSizer(wx.VERTICAL)
        sizer_magnification_scale = wx.BoxSizer(wx.VERTICAL)
        sizer_circle_size.Add(sizer_radius_scale, 1, wx.EXPAND, 0)
        sizer_circle_size.Add(sizer_magnification_scale, 1, wx.EXPAND, 0)

        s_text_rs = wx.StaticText(self.panel, wx.ID_ANY, 'ARV->半径の変換スケール')
        sizer_radius_scale.Add(s_text_rs, 1, wx.EXPAND, 0)

        sizer_rs_radio = wx.BoxSizer(wx.HORIZONTAL)
        sizer_radius_scale.Add(sizer_rs_radio, 1, wx.EXPAND, 0)

        self.RB_Log = wx.RadioButton(
            self.panel, wx.ID_ANY, '対数', style=wx.RB_GROUP)
        self.RB_Linear = wx.RadioButton(self.panel, wx.ID_ANY, '線形')

        if self.emgdata.radiusscale == RadiusScale.LOGARITHMIC:
            self.RB_Log.SetValue(True)
        elif self.emgdata.radiusscale == RadiusScale.LINEAR:
            self.RB_Linear.SetValue(True)
        else:
            self.RB_Log.SetValue(True)

        sizer_rs_radio.Add(self.RB_Log, 1, wx.EXPAND, 0)
        sizer_rs_radio.Add(self.RB_Linear, 1, wx.EXPAND, 0)

        s_text_ms = wx.StaticText(self.panel, wx.ID_ANY, '円の拡大率')
        self.spinctrldouble_ms = wx.SpinCtrlDouble(
            self.panel, wx.ID_ANY, value=str(self.emgdata.magscale), max=100.0, min=1.0)
        sizer_magnification_scale.Add(s_text_ms, flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_magnification_scale.Add(
            self.spinctrldouble_ms, flag=wx.ALIGN_CENTER | wx.TOP)

        #############################
        # Lower Buttons
        #############################
        sizer_lowerbutton = wx.BoxSizer(wx.HORIZONTAL)
        sizer_whole.Add(sizer_lowerbutton, 1, wx.EXPAND, 0)

        self.button_Confirmconfig = wx.Button(self.panel, wx.ID_ANY, "適用")
        self.button_Exit = wx.Button(self.panel, wx.ID_ANY, u"閉じる")

        sizer_lowerbutton.Add(self.button_Confirmconfig, 1, 0)
        sizer_lowerbutton.Add(self.button_Exit, 1, 0)

        self.panel.SetSizer(sizer_whole)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.OnButtonConfirmConfig,
                  self.button_Confirmconfig)
        self.Bind(wx.EVT_BUTTON, self.OnButtonExit, self.button_Exit)

    def OnButtonConfirmConfig(self, event):
        # Timer
        self.emgdata.hours = self.spinctrl_h.GetValue()
        self.emgdata.minutes = self.spinctrl_m.GetValue()
        self.emgdata.seconds = self.spinctrl_s.GetValue()

        try:
            sendCommandBuff = classPacket.getSendCommand_SetTimer(
                self.emgdata.targetSenssorModuleId, self.emgdata.hours, self.emgdata.minutes, self.emgdata.seconds)
            self.SerialPort.sendPacket(sendCommandBuff)
        except:
            print("Error: Timer setting failed. Please check the connection.")

        # Connection mode
        if self.RB_40hz.GetValue():
            self.emgdata.measureMode = 0x55
        elif self.RB_20hz.GetValue():
            self.emgdata.measureMode = 0x45
        else:
            self.emgdata.measureMode = 0x35

        # Circle color
        if self.RB_RED.GetValue():
            self.emgdata.circlecolor_id = CircleColorID.RED
            self.emgdata.circlecolor = (0, 0, 255)
        else:
            self.emgdata.circlecolor_id = CircleColorID.BLACK
            self.emgdata.circlecolor = (0, 0, 0)

        # Circle size (radius scale)
        if self.RB_Log.GetValue():
            self.emgdata.radiusscale = RadiusScale.LOGARITHMIC
        else:
            self.emgdata.radiusscale = RadiusScale.LINEAR

        # Circle size (magnification scale)
        self.emgdata.magscale = self.spinctrldouble_ms.GetValue()

        print("measuremode: ",self.emgdata.measureMode)
        print("circlecolor_id: ",self.emgdata.circlecolor_id)
        print("radiusscale: ",self.emgdata.radiusscale)
        print("magscale: ",self.emgdata.magscale)

        wx.MessageBox("設定が完了しました", u"設定完了", style=wx.OK)

    def OnButtonExit(self, event):  # 設定画面を閉じる
        self.Destroy()

    def ExitHandler(self, event):
        self.Destroy()


class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()

        thread_rs = threading.Thread(target=self.realsense_render, daemon=True)
        thread_rs.start()

        return True

    def render_ids_3d(self, render_image, skeletons_2d, depth_map, depth_intrinsic, joint_confidence):
        thickness = 1
        text_color = (255, 255, 255)
        circle_color = (0, 0, 255)

        rows, cols, channel = render_image.shape[:3]
        distance_kernel_size = 5

        log_r = np.math.log(abs(self.frame.emgdata.emg_data)+1.0, 1.1)
        mag = 5.0
        cv2.circle(render_image,
                   (100, 100),
                   int(np.ceil(log_r*mag)),
                   (0, 0, 255),
                   -1,
                   )

        # calculate 3D keypoints and display them
        for skeleton_index in range(len(skeletons_2d)):
            skeleton_2D = skeletons_2d[skeleton_index]
            joints_2D = skeleton_2D.joints
            did_once = False
            for joint_index in range(len(joints_2D)):
                # if not joint_index == 1:
                #     continue

                # if did_once == False:
                #     # cv2.putText(
                #     #     render_image,
                #     #     "id: " + str(skeleton_2D.id),
                #     #     (int(joints_2D[joint_index].x), int(
                #     #         joints_2D[joint_index].y - 30)),
                #     #     cv2.FONT_HERSHEY_SIMPLEX,
                #     #     0.55,
                #     #     text_color,
                #     #     thickness,
                #     # )
                #     did_once = True
                # check if the joint was detected and has valid coordinate
                if skeleton_2D.confidences[joint_index] > joint_confidence:
                    # distance_in_kernel = []
                    # low_bound_x = max(
                    #     0,
                    #     int(
                    #         joints_2D[joint_index].x -
                    #         math.floor(distance_kernel_size / 2)
                    #     ),
                    # )
                    # upper_bound_x = min(
                    #     cols - 1,
                    #     int(joints_2D[joint_index].x +
                    #         math.ceil(distance_kernel_size / 2)),
                    # )
                    # low_bound_y = max(
                    #     0,
                    #     int(
                    #         joints_2D[joint_index].y -
                    #         math.floor(distance_kernel_size / 2)
                    #     ),
                    # )
                    # upper_bound_y = min(
                    #     rows - 1,
                    #     int(joints_2D[joint_index].y +
                    #         math.ceil(distance_kernel_size / 2)),
                    # )
                    # for x in range(low_bound_x, upper_bound_x):
                    #     for y in range(low_bound_y, upper_bound_y):
                    #         distance_in_kernel.append(
                    #             depth_map.get_distance(x, y))
                    # median_distance = np.percentile(
                    #     np.array(distance_in_kernel), 50)
                    # depth_pixel = [
                    #     int(joints_2D[joint_index].x),
                    #     int(joints_2D[joint_index].y),
                    # ]
                    # if median_distance >= 0.3:
                    #     point_3d = rs.rs2_deproject_pixel_to_point(
                    #         depth_intrinsic, depth_pixel, median_distance
                    #     )
                    #     point_3d = np.round([float(i) for i in point_3d], 3)
                    #     point_str = [str(x) for x in point_3d]
                    #     cv2.putText(
                    #         render_image,
                    #         str(point_3d),
                    #         (int(joints_2D[joint_index].x),
                    #          int(joints_2D[joint_index].y)),
                    #         cv2.FONT_HERSHEY_DUPLEX,
                    #         0.4,
                    #         text_color,
                    #         thickness,
                    #     )

                    if joint_index == 1:
                        cv2.circle(
                            render_image,
                            (int(joints_2D[joint_index].x),
                             int(joints_2D[joint_index].y)),
                            int(np.ceil(log_r*mag)),
                            circle_color,
                            -1,
                        )

    def realsense_render(self):
        try:
            # Configure depth and color streams of the intel realsense
            config = rs.config()
            config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 1280,
                                 720, rs.format.rgb8, 30)

            if not os.path.exists('data'):
                os.makedirs('data')

            # config.enable_record_to_file(os.path.join('data', 'data.mp4'))

            # Start the realsense pipeline
            pipeline = rs.pipeline()
            pipeline.start(config)

            # Create align object to align depth frames to color frames
            align = rs.align(rs.stream.color)

            # Get the intrinsics information for calculation of 3D point
            unaligned_frames = pipeline.wait_for_frames()
            frames = align.process(unaligned_frames)
            depth = frames.get_depth_frame()
            depth_intrinsic = depth.profile.as_video_stream_profile().intrinsics

            # Initialize the cubemos api with a valid license key in default_license_dir()
            skeletrack = skeletontracker(cloud_tracking_api_key="")
            joint_confidence = 0.2

            # Create window for initialisation
            window_name = "cubemos skeleton tracking with realsense D400 series"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL +
                            cv2.WINDOW_KEEPRATIO)

            while True:
                # Create a pipeline object. This object configures the streaming camera and owns it's handle
                unaligned_frames = pipeline.wait_for_frames()
                frames = align.process(unaligned_frames)
                depth = frames.get_depth_frame()
                color = frames.get_color_frame()
                if not depth or not color:
                    continue

                # Convert images to numpy arrays
                depth_image = np.asanyarray(depth.get_data())
                color_image = np.asanyarray(color.get_data())

                # perform inference and update the tracking id
                skeletons = skeletrack.track_skeletons(color_image)

                # render the skeletons on top of the acquired image and display it
                color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
                cm.render_result(skeletons, color_image, joint_confidence)
                # # self.render_ids_3d(
                # #     color_image, skeletons, depth, depth_intrinsic, joint_confidence
                # # )

                # calculate 3D keypoints and display them
                for skeleton_index in range(len(skeletons)):
                    skeleton_2D = skeletons[skeleton_index]
                    joints_2D = skeleton_2D.joints

                    for joint_index in range(len(joints_2D)):
                        if skeleton_2D.confidences[joint_index] > joint_confidence:
                            if joint_index == 1:

                                radius = 0

                                if self.frame.emgdata.radiusscale == RadiusScale.LOGARITHMIC:
                                    radius = np.math.log(
                                        abs(self.frame.emgdata.emg_data)+1.0, 1.1)
                                else:
                                    radius = abs(self.frame.emgdata.emg_data)

                                cv2.circle(
                                    color_image,
                                    (int(joints_2D[joint_index].x),
                                     int(joints_2D[joint_index].y)),
                                    int(np.ceil(radius*self.frame.emgdata.magscale)),
                                    self.frame.emgdata.circlecolor,
                                    -1,
                                )

                cv2.imshow(window_name, color_image)
                if cv2.waitKey(1) == 27:
                    break

            pipeline.stop()
            cv2.destroyAllWindows()

        except Exception as ex:
            print('Exception occured: "{}"'.format(ex))


if __name__ == "__main__":

    # thread_rs = threading.Thread(target=realsense_render)
    # thread_rs.start()

    app = MyApp(0)
    app.MainLoop()

    # thread_app = threading.Thread(target=app.MainLoop())
    # thread_app.start()

    # thread_rs.join()
    # thread_app.join()
