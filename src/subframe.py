import wx
import classPacket  # ;
from enum import Enum

# (半)円の色
class CircleColorID(Enum):
    RED = 0
    BLACK = 1

#     BLUE = 2
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
                self.emgdata.targetSenssorModuleId, self.emgdata.hours, self.emgdata.minutes, self.emgdata.seconds, self.emgdata.calibration_time)
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
            self.emgdata.circlecolor_front = (255, 0, 0)
            self.emgdata.circlecolor_back = (0, 0, 255)
        else:
            self.emgdata.circlecolor_id = CircleColorID.BLACK
            self.emgdata.circlecolor_front = (0, 0, 0)
            self.emgdata.circlecolor_back = (255, 255, 255)


        # Circle size (magnification scale)
        self.emgdata.magscale = self.spinctrldouble_ms.GetValue()

        print("measuremode: ", self.emgdata.measureMode)
        print("circlecolor_id: ", self.emgdata.circlecolor_id)
        print("magscale: ", self.emgdata.magscale)

        wx.MessageBox("設定が完了しました", u"設定完了", style=wx.OK)

    def OnButtonExit(self, event):  # 設定画面を閉じる
        self.Destroy()

    def ExitHandler(self, event):
        self.Destroy()