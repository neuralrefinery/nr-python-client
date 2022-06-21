import zmq
import cv2
import json
import datetime

token = "VjKcluID6w170FcBjxJ9"

if __name__=="__main__" :

    context = zmq.Context(1)
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://localhost:5555')

    cap = cv2.VideoCapture(0)
    assert cap.isOpened()

    while True :
        ret, frame = cap.read()

        if ret :
            sframe = cv2.resize( frame, None, None, 0.25, 0.25 )
            
            ts = datetime.datetime.now()
            ts_str = ts.strftime('%Y%m%d%H%M%S%f')

            info = {}
            info['reference'] = 'local'
            info['process_token'] = token
            info['stream_id'] = 'some_id'
            info['timestamp'] = ts_str
            info['shape'] = list(sframe.shape)

            info = json.dumps( info ).encode()
            data = sframe.tobytes()

            socket.send( info, zmq.SNDMORE )
            socket.send( data )

            print( socket.recv() )
    #pass
