import zmq
import time
import threading
import queue
import cv2
import json


class SubmitThread( threading.Thread ):
    def __init__( self, context, server, idx, submit_queue, mutex, reference_dict ):
        super().__init__()

        self._idx = idx
        self._submit_queue = submit_queue
        self._mutex = mutex
        self._reference_dict = reference_dict

        self._socket = zmq.Socket( context, zmq.REQ )
        self._socket.connect("%s:33000" % (server) )

        self._should_stop = threading.Event()

    def _submit( self, frame, process_token, stream_id, upload_scale ):
        t0 = time.time()
        frame = cv2.resize( frame, None, None, upload_scale, upload_scale )

        ret, encoded = cv2.imencode( '.jpg', frame )
        encoded = encoded.tobytes()

        info = {}
        info["Data-Size"] = len(encoded)
        info["process_token"] = process_token;
        info["stream_id"] = stream_id;

        self._socket.send(json.dumps(info).encode(), zmq.SNDMORE )
        self._socket.send(encoded)
        ref = self._socket.recv()

        t1 = time.time()

        print( t1 - t0 )

        return ref

    def stop( self ):
        self._should_stop.set()

    def run( self ):

        while not self._should_stop.is_set() :
            data = None
            self._mutex.acquire()

            if not self._submit_queue.empty():
                data = self._submit_queue.get()

            self._mutex.release()

            if data is not None :
                ref = self._submit( data['frame'], data['process_token'], data['stream_id'],
                                    data['upload_scale'] )
                self._reference_dict[data['timestamp']] = ref

            time.sleep(0.001)

class FetchThread( threading.Thread ):
    def __init__( self, context, server, idx, fetch_queue, mutex, delay, reference_dict, draw_queue ):
        super().__init__()

        self._idx = idx
        self._fetch_queue = fetch_queue
        self._mutex = mutex
        self._delay = delay
        self._reference_dict = reference_dict
        self._draw_queue = draw_queue

        self._socket = zmq.Socket( context, zmq.REQ )
        self._socket.connect("%s:33001" % ( server ))

        self._should_stop = threading.Event()

    def _fetch( self, reference ):
        self._socket.send( reference )
        results = self._socket.recv()
        return results

    def stop( self ):
        self._should_stop.set()

    def run( self ):
        while not self._should_stop.is_set() :
            self._mutex.acquire()

            data = None
            if not self._fetch_queue.empty() :
                t1 = time.time()

                if t1 - self._fetch_queue.queue[0]['time'] >= self._delay :
                    data = self._fetch_queue.get()

            self._mutex.release()

            if data is not None :
                ts = data['timestamp']
                print( time.time() - data['time'] )
                if not ts in self._reference_dict :
                    print("Not found")
                else :
                    ref = self._reference_dict[ts]
                    res = self._fetch(ref)

                    data['meta'] = json.loads(res)
                    self._draw_queue.put(data)

                    del self._reference_dict[ts]
            else :
                time.sleep(0.001)

class Module :
    def __init__( self, server, num_submitters, num_fetchers, delay, draw_queue ):
        super().__init__()

        self._context = zmq.Context(1)

        self._submitters = []
        self._fetchers = []

        self._submit_queue = queue.Queue()
        self._submit_mutex = threading.Lock()

        self._reference_dict = {}

        for idx in range( num_submitters ):
            p = SubmitThread( self._context, server, idx, self._submit_queue, self._submit_mutex,
                              self._reference_dict )
            p.start()
            self._submitters.append(p)

        self._fetch_queue = queue.Queue()
        self._fetch_mutex = threading.Lock()

        for idx in range( num_fetchers ):
            p = FetchThread( self._context, server, idx, self._fetch_queue, self._fetch_mutex, delay,
                             self._reference_dict, draw_queue )
            p.start()
            self._fetchers.append(p)

    def __del__( self ):
        for p in self._submitters :
            p.stop()
        for p in self._fetchers :
            p.stop()

        print("Bye!")

    def stop( self ):
        for p in self._submitters :
            p.stop()
        for p in self._fetchers :
            p.stop()

    def add( self, data ):
        self._submit_queue.put( data )
        self._fetch_queue.put( data )
