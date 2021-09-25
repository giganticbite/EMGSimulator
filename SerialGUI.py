import wx
import threading
import time
import datetime
import classSerial;
import classPacket;
import struct
DEF_LOGTEXT_MAX = 32
# コマンドID	定義(必要に応じて追加)
DEF_SENDCOMMAND_ID_GETSTATUSINFO = 5
DEF_SENDCOMMAND_ID_PREMEASURE = 31
DEF_SENDCOMMAND_ID_STARTMEASURE = 2
DEF_SENDCOMMAND_ID_ENDMEASURE = 4

##ログ管理用オブジェクト
#	ログを貯めておくオブジェクト
class LogText(object):

	##コンストラクタ
	#	@return	なし
	#	@param	self 		The object pointer.
	#	@param	txt 		ログ文字列
	def __init__(self,txt):
		##発生時間
		self.mDate = datetime.datetime.now()
		##ログ文字列
		self.mText = txt

	
	##	ログ文字列取得
	#	@return	ログ文字列
	#	@param	self 			:The object pointer.
	#	@param	isDisplayTime 	:時間表示をつけるか？
	#							 True:つける　　False:つけない
	def getLog( self, isDisplayTime ):
		lineText = ""
		if	isDisplayTime==True:
			#時間を加える
			lineText += str(self.mDate.year) + "/" + str(self.mDate.month) + "/" + str(self.mDate.day)
			lineText += " " + str(self.mDate.hour) + ":" + str(self.mDate.minute)+ ":" + str(self.mDate.second)
		lineText += " > " + self.mText
		return lineText



class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((416, 300))
        self.SetTitle("frame")

        self.panel = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)

        self.combo_box_Serialport = wx.ComboBox(self.panel, wx.ID_ANY, choices=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7"], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        sizer_2.Add(self.combo_box_Serialport, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Connect = wx.Button(self.panel, wx.ID_ANY, u"接続")
        sizer_2.Add(self.button_Connect, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Prepare = wx.Button(self.panel, wx.ID_ANY, u"計測準備")
        sizer_2.Add(self.button_Prepare, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.button_Start = wx.Button(self.panel, wx.ID_ANY, u"計測開始")
        sizer_2.Add(self.button_Start, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_3, 2, wx.EXPAND, 0)

        self.text_Receive = wx.TextCtrl(self.panel, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.text_Receive.SetMinSize((320, 150))
        sizer_3.Add(self.text_Receive, 4, wx.ALL | wx.EXPAND, 4)

        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_5, 1, wx.EXPAND, 0)

        self.text_Emg = wx.TextCtrl(self.panel, wx.ID_ANY, "")
        sizer_5.Add(self.text_Emg, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)

#        self.gauge_1 = wx.Gauge(self.panel, wx.ID_ANY, range=200, style=wx.GA_HORIZONTAL)
#        sizer_5.Add(self.gauge_1, 3, wx.ALL | wx.EXPAND, 4)
        self.panel_1 = wx.Panel(self.panel, wx.ID_ANY)
        sizer_5.Add(self.panel_1, 3, wx.ALL | wx.EXPAND, 4)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_4, 1, wx.EXPAND, 0)

        sizer_4.Add((150, 20), 2, 0, 0)

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
        # end wxGlade


        self.StringPortName = "COM3"
        self.ListLog = []

        self.SerialPort = classSerial.SerialPort()#シリアルポート    ##	スレッド実行中か？
    #	True:実行中		False:それ以外
    mbIsRunningThread = False

    ##	スレッドの終了待ち中か？
    #	True:処理終了待ち中		False:それ以外
    mbIsWaitThread = False

    def stopThreadReceive(self):
        if	self.mbIsRunningThread==True:
        #スレッドが走っている状態であれば、終了待ちを行う
            self.mbIsWaitThread = True
            self.mbIsRunningThread = False
            self.th = None

    def startThreadReceive(self):
        #起動中のスレッド停止
        self.stopThreadReceive()
        self.mbIsRunningThread = True
        #self.main_thread = threading.current_thread()
        self.th = threading.Thread(target=self.ReceivePacketASync,name="thr1",args=())
        self.th.setDaemon(True)
        self.th.start()

    ##ログを追加
    #    @return        なし
    #    
    #    @param        self         :    The object pointer.
    #    @param        logString    :    追加するログ文字列
    def addLog(self,logString):
        #一定数以上を超えないように、古いログから削除
        if    DEF_LOGTEXT_MAX<len(self.ListLog):
            del self.ListLog[0]

        #ログを追加
        #newLog = LogText(logString)
        #self.ListLog.append(newLog)
        self.ListLog.append(logString)
        #ログを更新
        self.updateMessage()
    

    def updateMessage(self):
        for log in self.ListLog:
            self.text_Receive.AppendText(log+'\n')

    ##パケットの受信待ち    スレッド処理
    #        スレッドから呼び出される
    #    @return        なし
    #    @param        self :    The object pointer.
    def ReceivePacketASync(self):
        self.addLog( u"データ受信待ちスレッド開始" )

        # else分岐処理を残しておきたいための変数
        dmyCnt=0
        
        #受信データ取得
        while    self.mbIsRunningThread==True:
            if    self.SerialPort.isEnableAccess()==True:
                packetBuff = self.SerialPort.receiveBufferASync()
                if packetBuff != 0 and packetBuff.hex()[10]=="8"and packetBuff.hex()[11]=="3":
                    emg_data=round(struct.unpack_from(b'>f',packetBuff,11)[0],2)
                    #print(str(emg_data))
                    self.text_Emg.Clear()#筋電データクリア
                    self.text_Emg.AppendText(str(emg_data))#新しいデータをappend

                    dc=dc = wx.PaintDC(self.panel_1)
                    dc.SetPen(wx.Pen('blue'))
                    dc.SetBrush(wx.Brush('blue'))
                    dc.DrawRectangle(0,0,int(emg_data*20+100),20)

                    self.addLog("\n")
                    
                    #受信データ解析
                    resultDic = classPacket.AnalyzePacketThread( packetBuff )
                    #print "Result:",resultDic
                    
                    if    0<len(resultDic):
                        self.addLog( u"受信成功" )
                        if    'ack' in resultDic:
                            ack = resultDic['ack']
                            if    ack!=None:
                                self.addLog( ack.getString() )
                        
                        if    'dat' in resultDic:
                            dat = resultDic['dat']
                            if    dat!=None:
                                self.addLog( dat.getResultByString() )

                    else:
                        #self.addLog( u"受信失敗" )
                        dmyCnt+=1

                else:
                    dmyCnt+=1
                    #print "running ReceivePacketASync..."

            else:
                #ポートが無効なので、いったん停止
                time.sleep(2)
                print("running ReceivePacketASync")

        print("finish ReceivePacketASync")
        self.addLog( u"データ受信待ちスレッド終了" )
        self.mbIsWaitThread = False


    def OnButtonConnect(self, event):  # 接続
        bIsOpen = True
        if	self.SerialPort.isEnableAccess()==True:
        #すでに、PortOpen済みなので閉じる処理を行う
            bIsOpen = False
        else:
		#ポートが無効なので、開く処理
            bIsOpen = True

        if	bIsOpen==True:
        #ポート開く処理を開始
            #self.SerialPort.portOpen(self.EntryPortName.get())
            self.StringPortName = self.combo_box_Serialport.GetValue()
            print("portPath:",self.StringPortName)
            self.SerialPort.portOpen(self.StringPortName)
            if	self.SerialPort.isEnableAccess()==True:
                #アクセス開始できたので、受信スレッド開始
                self.startThreadReceive()
                self.button_Connect.SetLabel("切断")
            else:
            #portが開けなかった
                wx.MessageBox(u"portが開けませんでした\nポートのパス:"+self.StringPortName,u"ポートエラー", style = wx.YES_NO)
        else:
        #ポート閉じる処理を開始
            self.stopThreadReceive()
            self.addLog( "Port Close:" + self.SerialPort.mDeviceName )
            self.button_Connect.SetLabel("接続")

    def OnButtonPrepare(self, event):  # 計測準備
        sendCommandBuff = classPacket.getSendCommand( DEF_SENDCOMMAND_ID_PREMEASURE, 1 ) #コマンド値, ターゲットID
        self.SerialPort.sendPacket( sendCommandBuff )

    def OnButtonStart(self, event):  # 計測開始
        sendCommandBuff = classPacket.getSendCommand( DEF_SENDCOMMAND_ID_STARTMEASURE, 1 ) #コマンド値, ターゲットID
        self.SerialPort.sendPacket( sendCommandBuff )

    def OnButonEnd(self, event):  # 計測終了
        sendCommandBuff = classPacket.getSendCommand( DEF_SENDCOMMAND_ID_ENDMEASURE, 1 ) #コマンド値, ターゲットID
        self.SerialPort.sendPacket( sendCommandBuff )

    def OnButtonExit(self, event):  # プログラム終了

        if	self.SerialPort.isEnableAccess()==True:
            self.stopThreadReceive()
            self.addLog( "Port Close:" + self.SerialPort.mDeviceName )
            self.button_Connect.SetLabel("接続")
        exit()
# end of class MyFrame

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
