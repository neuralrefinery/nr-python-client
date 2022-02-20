import wx
import os
import cv2
import numpy as np
from nr import Params, api
import datetime
import time
import threading
from queue import Queue, Empty
from drawer import drawer
import json

def process_image( image, api, drawer, params, queue, timestamp ):
    upload_scale = params.upload_scale
    simage = cv2.resize( image, None, None, upload_scale, upload_scale )

    process = {}
    process['token'] = params.process_token
    process['id'] = params.id_token
    process['image_scale'] = float(upload_scale)
    process['compliments'] = {}

    response = api.process(simage, process)

    response = json.loads( response.content )
    reference = response['reference']

    #print( reference )

    time.sleep(0.5)

    results = api.results( reference )

    if results.status_code == 200 :
        meta = json.loads(results.content)

        print( meta )

        if meta['status'] == 'OK' :
            image = drawer.draw(image,meta.get('results',{}), use_image=params.use_image)

        data = {}
        data["image"] = image
        data["timestamp"] = timestamp
        queue.put(data)

class CameraThread(threading.Thread):
    def __init__( self, auth, params, panel_shape ):
        super().__init__()

        self._auth = auth
        self._params = params
        self._frames_queue = Queue()
        self._api = api()
        self._panel_shape = panel_shape
         
        self._stop_event = threading.Event()

    def stop( self ):
        return self._stop_event.set()

    def stopped( self ):
        return self._stop_event.is_set()

    @property
    def frames_queue( self ):
        return self._frames_queue

    def run( self ):
        cap = cv2.VideoCapture(0)

        if cap.isOpened() :

            interval = 1.0 / self._params.fps
            start_time = time.time()
            diff_time = 0

            while not self._stop_event.is_set() :
                ret, frame = cap.read()

                if ret :
                    current_time = time.time()
                    if current_time - start_time + diff_time >= interval :
                        diff_time = max( [ current_time - start_time - interval, 0.0 ] )
                        start_time = current_time

                        height, width = frame.shape[:2]
                        frameWidth, frameHeight = self._panel_shape
                        scale = frameWidth / np.max( [ height, width ] )

                        dd = drawer( self._params.upload_scale, scale )

                        t = threading.Thread( target=process_image,
                                              args=( frame, self._api, dd, self._params, 
                                                     self._frames_queue, datetime.datetime.now() ) )
                                              
                        t.start()

        self._stop_event.set()

class FramePanel(wx.Panel):
    def __init__( self, parent, size ):
        super().__init__( parent, size=size )
        self._size = size
        self.SetBackgroundColour("GREEN")
        self.has_image = False
        #self.origin = [0,0]
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.last_time_stamp = datetime.datetime.now()
        self.draw_scale = 1.0

    def OnPaint(self, evt):
        if self.has_image :
            dc = wx.BufferedPaintDC(self)
            dc.DrawBitmap(self.bmp, 0,0 )

    def update( self, data ):#, meta, frame_time_stamp ):
        frame = data['image']
        frame_time_stamp = data['timestamp']
        if frame_time_stamp < self.last_time_stamp :
            return

        self.last_time_stamp = frame_time_stamp
        height, width = frame.shape[:2]
        frameWidth, frameHeight = self.Size
        
        scale = frameWidth / np.max( [ height, width ] )

        sframe = frame
        #sframe = cv2.resize( frame, None, None, scale, scale, 0 )
        sh, sw = sframe.shape[:2]

        sframe = cv2.cvtColor(sframe, cv2.COLOR_BGR2RGB)

        self.bmp = wx.Bitmap().FromBuffer(sw, sh, sframe)

        self.has_image = True
        self.Refresh()

class Interface(wx.Frame) :
    def __init__(self) :
        super().__init__( None, title="{NR} Webcam", style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN )

        if os.path.exists('config.local.yml') :
            self.params = Params('config.local.yml')
        else :
            self.params = Params('config.yml')

        if os.path.exists('auth.local.yml') :
            self.auth = Params('auth.local.yml')
        else :
            self.auth = Params('auth.yml')

        self.camera_thread = None

        self.create_controlls()
        self.do_layout()

        self.Bind( wx.EVT_CLOSE, self.on_close )
        self.Bind( wx.EVT_BUTTON, self.start, self.startButton )
        self.Bind( wx.EVT_BUTTON, self.stop, self.stopButton )

        self.timer = wx.Timer(self)
        self.timer.Start(1000./15.)
        self.Bind(wx.EVT_TIMER, self.timerUpdate)

    def on_close( self, event ):
        if self.camera_thread is not None :
            self.camera_thread.stop()
            self.camera_thread = None

        self.Destroy()

    def create_controlls( self ):
        self.urllabel = wx.StaticText(self, label="Server URL: ")
        self.urlentry = wx.TextCtrl(self, size=(200,-1), value=self.auth.server)
        self.usernamelabel = wx.StaticText(self, label="Username: ")
        self.usernameentry = wx.TextCtrl(self, size=(200,-1), value=self.auth.username)
        self.passwordlabel = wx.StaticText(self, label="Password: " )
        self.passwordentery = wx.TextCtrl(self, size=(200,-1), style = wx.TE_PASSWORD, value=self.auth.password)

        self.processTokenLabel = wx.StaticText(self, label="Process Token") 
        self.processTokenEntry = wx.TextCtrl( self, size=(200,-1), value=self.params.process_token )

        self.idTokenLabel = wx.StaticText(self, label="ID Token")
        self.idTokenEntry = wx.TextCtrl( self, size=(200,-1), value=self.params.id_token )

        self.uploadScaleLabel = wx.StaticText(self, label="Upload Scale")
        self.uploadScaleEntry = wx.TextCtrl( self, size=(200,-1), value=str(self.params.upload_scale) )

        self.drawScaleLabel = wx.StaticText(self, label="Draw Scale")
        self.drawScaleEntry = wx.TextCtrl( self, size=(200,-1), value=str(self.params.draw_scale) )
         
        self.fpsLabel = wx.StaticText(self, label="FPS")
        self.fpsEntry = wx.TextCtrl( self, size=(200,-1), value=str(self.params.fps) )

        self.useImageLabel = wx.StaticText(self, label="Use Image")
        self.useImageEntry = wx.CheckBox( self )
        self.useImageEntry.SetValue( self.params.use_image )

        
        self.startButton = wx.Button(self, label="Start Camera")
        self.stopButton = wx.Button(self, label="Stop Camera")

        self.panel = FramePanel( self, size=(600,400) )
        
    def do_layout( self ):

        # A horizontal BoxSizer will contain the GridSizer (on the left)
        # and the logger text control (on the right):
        mainSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        
        
        
        #gridSizerRight = wx.FlexGridSizer(rows=50, cols=1, vgap=10, hgap=10)

        # Prepare some reusable arguments for calling sizer.Add():
        expandOption = dict(flag=wx.EXPAND)
        noOptions = dict()
        emptySpace = ((0, 0), noOptions)

        # A GridSizer will contain the other controls:
        gridSizerLeft = wx.FlexGridSizer(rows=50, cols=2, vgap=2, hgap=10)

        # Add the controls to the sizers:
        for control, options in \
                [(self.urllabel, noOptions),
                 (self.urlentry, expandOption),
                 (self.usernamelabel, noOptions),
                 (self.usernameentry, expandOption),
                 (self.passwordlabel, noOptions),
                 (self.passwordentery, expandOption),
                 emptySpace,
                 emptySpace,

                 (self.processTokenLabel, noOptions),
                 (self.processTokenEntry, expandOption ),
                 (self.idTokenLabel, noOptions),
                 (self.idTokenEntry, expandOption),

                 (self.uploadScaleLabel, noOptions),
                 (self.uploadScaleEntry, expandOption),
                 (self.drawScaleLabel, noOptions),
                 (self.drawScaleEntry, expandOption),
                 
                 (self.fpsLabel, noOptions),
                 (self.fpsEntry, expandOption),

                 (self.useImageLabel, noOptions ),
                 (self.useImageEntry, expandOption ),
                 emptySpace,
                 ( self.startButton, expandOption ),
                 emptySpace,
                 ( self.stopButton, expandOption ),
                
                 ]:
            gridSizerLeft.Add(control, **options)

        for control, options in \
                [
                    (gridSizerLeft, dict(border=10, flag=wx.EXPAND | wx.ALL) ),
                    (self.panel, dict( border=10, flag=wx.EXPAND | wx.ALL, proportion=1)),
                ]:
            mainSizer.Add(control, **options)

        self.SetSizerAndFit(mainSizer)
        self.SetAutoLayout(True)

    def start( self, event ):
        self.auth.set("server", self.urlentry.GetValue())
        self.auth.set("username", self.usernameentry.GetValue())
        self.auth.set("password", self.passwordentery.GetValue())

        self.params.set("process_token", self.processTokenEntry.GetValue())
        self.params.set("id_token", self.idTokenEntry.GetValue())
        self.params.set("upload_scale", float(self.uploadScaleEntry.GetValue()))
        self.params.set("draw_scale", float(self.drawScaleEntry.GetValue()))
        self.params.set("fps", int(self.fpsEntry.GetValue()))
        self.params.set("use_image", self.useImageEntry.GetValue())

        self.params.save('config.local.yml')
        self.auth.save('auth.local.yml')

        if self.camera_thread is not None :
            self.camera_thread.stop()
            self.camera_thread = None

        self.camera_thread = CameraThread( self.auth, self.params, self.panel.Size )
        self.camera_thread.start()

    def stop( self, event ):
        if self.camera_thread is not None :
            self.camera_thread.stop()
            self.camera_thread = None


    def timerUpdate( self, event ):
        if self.camera_thread is None :
            return
    
        if not self.camera_thread.frames_queue.empty() :
            frame = self.camera_thread.frames_queue.get()
            self.panel.update( frame )

if __name__=="__main__" :
    app = wx.App()
    window = Interface() 
    window.Show()
    app.MainLoop()
