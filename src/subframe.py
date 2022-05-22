import wx
import classPacket  # ;
from enum import Enum

# (半)円の色


class CircleColorID(Enum):
    RED = 0
    BLACK = 1

#     BLUE = 2
# Config Window

# 半円の向き(筋肉のついている側)


class CircleDirection(Enum):
    FRONT = 0
    BACK = 1


SENSOR_CONNECTION_MAX = 15


class SensorInfo:
    def __init__(self, max_radius_denominator, line_startpoint, line_endpoint, circle_direction):
        self.max_radius_denominator = max_radius_denominator

        self.line_startpoint = line_startpoint
        self.line_endpoint = line_endpoint

        self.emg_data_max = 0.0
        self.emg_data = 0.0
        self.emg_data_sequence = []
        self.circle_direction = circle_direction


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
        self.color_front_tmp = self.emgdata.circlecolor_front
        self.color_back_tmp = self.emgdata.circlecolor_back

        sizer_ll = wx.BoxSizer(wx.VERTICAL)
        sizer_lower.Add(sizer_ll, 1, wx.EXPAND, 0)

        s_text_ccdesc = wx.StaticText(
            self.panel, wx.ID_ANY, '半円の色')
        sizer_ll.Add(s_text_ccdesc, flag=wx.ALIGN_CENTER | wx.TOP, border=30)

        # front color
        sizer_front_color = wx.BoxSizer(wx.HORIZONTAL)
        sizer_ll.Add(sizer_front_color,
                     flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        self.button_front_color = wx.Button(self.panel, wx.ID_ANY, u"前側の色")
        sizer_front_color.Add(self.button_front_color, 1, wx.EXPAND, 0)

        # back color
        sizer_back_color = wx.BoxSizer(wx.HORIZONTAL)
        sizer_ll.Add(sizer_back_color, flag=wx.ALIGN_CENTER |
                     wx.TOP, border=20)
        self.button_back_color = wx.Button(self.panel, wx.ID_ANY, u"後側の色")
        sizer_back_color.Add(self.button_back_color, 1, wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.OnButtonSelectColor(is_front=True),
                  self.button_front_color)
        self.Bind(wx.EVT_BUTTON, self.OnButtonSelectColor(is_front=False),
                  self.button_back_color)

        # color preview
        self.front_color_preview = wx.StaticText(self.panel, wx.ID_ANY, "")
        self.front_color_preview.SetBackgroundColour(self.color_front_tmp)
        sizer_front_color.Add(self.front_color_preview, 1, wx.EXPAND, 0)

        self.back_color_preview = wx.StaticText(self.panel, wx.ID_ANY, "")
        self.back_color_preview.SetBackgroundColour(self.color_back_tmp)
        sizer_back_color.Add(self.back_color_preview, 1, wx.EXPAND, 0)

        #############################
        # Circle size (lower right)
        #############################
        sizer_lr = wx.BoxSizer(wx.VERTICAL)
        sizer_lower.Add(sizer_lr, 1, wx.EXPAND, 0)

        s_text_csdesc = wx.StaticText(
            self.panel, wx.ID_ANY, '半円のサイズとID')
        sizer_lr.Add(s_text_csdesc, flag=wx.ALIGN_CENTER | wx.TOP, border=30)

        self.button_circle_size_id = wx.Button(self.panel, wx.ID_ANY, u"設定を開く")
        self.Bind(wx.EVT_BUTTON, self.OnButtonRadiusandID,
                  self.button_circle_size_id)
        sizer_lr.Add(self.button_circle_size_id,
                     flag=wx.ALIGN_CENTER | wx.TOP, border=30)

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

    def OnButtonSelectColor(self, is_front):
        def OnButtonSelectColor_child(event):
            cd = wx.ColourDialog(None)
            cd.ShowModal()

            color = cd.GetColourData().GetColour()

            rgb = (color[:3])
            if is_front:
                self.color_front_tmp = rgb
                self.front_color_preview.SetBackgroundColour(
                    self.color_front_tmp)
            else:
                self.color_back_tmp = rgb
                self.back_color_preview.SetBackgroundColour(
                    self.color_back_tmp)

            self.Refresh()
        return OnButtonSelectColor_child

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
        self.emgdata.circlecolor_front = self.color_front_tmp
        self.emgdata.circlecolor_back = self.color_back_tmp

        wx.MessageBox("設定が完了しました", u"設定完了", style=wx.OK)

    def OnButtonExit(self, event):  # 設定画面を閉じる
        self.Destroy()

    def ExitHandler(self, event):
        self.Destroy()

    def OnButtonRadiusandID(self, event):
        RadiusandID(self.emgdata)


class RadiusandID(wx.Dialog):
    def __init__(self, emgdata):
        self.emgdata_RID = emgdata

        wx.Dialog.__init__(self, None, -1, "半径とID設定")
        self.SetSize((800, 900))

        self.SetWindowStyle_RID()
        self.Bind(wx.EVT_CLOSE, self.ExitHandler)

        self.ShowModal()

    def SetWindowStyle_RID(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        sizer_whole = wx.BoxSizer(wx.VERTICAL)

        sizer_upper = wx.BoxSizer(wx.VERTICAL)
        sizer_lower = wx.BoxSizer(wx.VERTICAL)
        sizer_whole.Add(sizer_upper, 1, wx.EXPAND, 0)
        sizer_whole.Add(sizer_lower, 1, wx.EXPAND, 0)

        #############################
        # Radius and ID setting (upper)
        #############################

        s_text_riddesc = wx.StaticText(self.panel, wx.ID_ANY, '半径とID')
        sizer_upper.Add(s_text_riddesc, flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_upper.Add(wx.StaticText(self.panel, wx.ID_ANY,
                                      '分母：半径の分母(1-4)'), flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_upper.Add(wx.StaticText(self.panel, wx.ID_ANY,
                                      '半径=線分長/半径分母\n'), flag=wx.ALIGN_CENTER | wx.TOP)
        sizer_upper.Add(wx.StaticText(self.panel, wx.ID_ANY,
                                      '始点,終点：半円の始点と終点のID(0-32, 下図参照)\n'), flag=wx.ALIGN_CENTER | wx.TOP)

        self.spinctrl_rd = []
        self.spinctrl_start = []
        self.spinctrl_end = []

        self.RB_front = []
        self.RB_back = []

        idperrow = 4
        for idx in range(0, SENSOR_CONNECTION_MAX+1, idperrow):
            sizer_rid_2 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_upper.Add(sizer_rid_2, 1, wx.EXPAND)

            for i in range(idperrow):
                sizer_rid_selector = wx.BoxSizer(wx.HORIZONTAL)
                sizer_radius_denominator = wx.BoxSizer(wx.VERTICAL)
                sizer_start_id = wx.BoxSizer(wx.VERTICAL)
                sizer_end_id = wx.BoxSizer(wx.VERTICAL)

                sizer_rid_selector.Add(
                    sizer_radius_denominator, 1, wx.EXPAND, 0)
                sizer_rid_selector.Add(
                    sizer_start_id, 1, wx.EXPAND, 0)
                sizer_rid_selector.Add(
                    sizer_end_id, 1, wx.EXPAND, 0)

                # get times set before or default
                rd, start, end, circle_direction = self.emgdata_RID.GetSetRID(
                    idx+i)

                s_text_rd = wx.StaticText(self.panel, wx.ID_ANY, '分母')
                self.spinctrl_rd.append(wx.SpinCtrl(
                    self.panel, wx.ID_ANY, value=str(rd), min=1, max=4))
                sizer_radius_denominator.Add(
                    s_text_rd, flag=wx.ALIGN_CENTER | wx.TOP)
                sizer_radius_denominator.Add(
                    self.spinctrl_rd[-1], flag=wx.ALIGN_CENTER | wx.TOP)

                s_text_start = wx.StaticText(
                    self.panel, wx.ID_ANY, '始点')
                self.spinctrl_start.append(wx.SpinCtrl(
                    self.panel, wx.ID_ANY, value=str(start), max=32))
                sizer_start_id.Add(
                    s_text_start, flag=wx.ALIGN_CENTER | wx.TOP)
                sizer_start_id.Add(self.spinctrl_start[-1],
                                   flag=wx.ALIGN_CENTER | wx.TOP)

                s_text_end = wx.StaticText(
                    self.panel, wx.ID_ANY, '終点')
                self.spinctrl_end.append(wx.SpinCtrl(
                    self.panel, wx.ID_ANY, value=str(end), max=32))
                sizer_end_id.Add(s_text_end, flag=wx.ALIGN_CENTER | wx.TOP)
                sizer_end_id.Add(self.spinctrl_end[-1],
                                 flag=wx.ALIGN_CENTER | wx.TOP)

                # set front or back
                self.RB_front.append(wx.RadioButton(
                    self.panel, wx.ID_ANY, '前', style=wx.RB_GROUP))
                self.RB_back.append(wx.RadioButton(
                    self.panel, wx.ID_ANY, '後'))
                sizer_rid_selector.Add(self.RB_front[-1], 1, wx.EXPAND, 0)
                sizer_rid_selector.Add(self.RB_back[-1], 1, wx.EXPAND, 0)

                if circle_direction == CircleDirection.FRONT:
                    self.RB_front[-1].SetValue(True)
                else:
                    self.RB_back[-1].SetValue(True)

                sizer_rid = wx.BoxSizer(wx.VERTICAL)
                s_text_id = wx.StaticText(
                    self.panel, wx.ID_ANY, "SensorID:"+str(idx+i+1))
                sizer_rid.Add(s_text_id, flag=wx.ALIGN_CENTER |
                              wx.TOP)
                sizer_rid.Add(sizer_rid_selector, flag=wx.ALIGN_CENTER |
                              wx.TOP)

                sizer_rid_2.Add(sizer_rid, 1, wx.EXPAND)

        #############################
        # image (lower)
        #############################
        s_text_IDpicdesc = wx.StaticText(self.panel, wx.ID_ANY, 'ID対応図')
        sizer_lower.Add(s_text_IDpicdesc,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=30)
        try:
            image = wx.Image('body_landmarks.png')
            self.bitmap = image.ConvertToBitmap()

            sb_image = wx.StaticBitmap(
                self.panel, wx.ID_ANY, self.bitmap, (0, 0))
            sizer_lower.Add(sb_image, flag=wx.EXPAND)
            # sizer_lower.Add(sb_image, 1, wx.EXPAND, 0)
        except:
            print('ERROR: Cannot load image')
            pass

        #############################
        # Lower Buttons
        #############################
        sizer_lowerbutton = wx.BoxSizer(wx.HORIZONTAL)
        sizer_whole.Add(sizer_lowerbutton, 1, wx.EXPAND, border=30)

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
        for idx in range(SENSOR_CONNECTION_MAX):

            rd = self.spinctrl_rd[idx].GetValue()
            sid = self.spinctrl_start[idx].GetValue()
            eid = self.spinctrl_end[idx].GetValue()

            self.emgdata_RID.emg_datalist[idx].line_startpoint = sid
            self.emgdata_RID.emg_datalist[idx].line_endpoint = eid
            self.emgdata_RID.emg_datalist[idx].max_radius_denominator = rd

            if self.RB_front[idx].GetValue():
                self.emgdata_RID.emg_datalist[idx].circle_direction = CircleDirection.FRONT
            else:
                self.emgdata_RID.emg_datalist[idx].circle_direction = CircleDirection.BACK

        wx.MessageBox("設定が完了しました", u"設定完了", style=wx.OK)

    def OnButtonExit(self, event):  # 設定画面を閉じる
        self.Destroy()

    def ExitHandler(self, event):
        self.Destroy()
