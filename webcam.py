import os
import requests
import cv2
import json
import time
import threading
from queue import Queue

from nr import Params, api
from pprint import pprint

from drawer import drawer

nr_api = api()

def process_image( image, params, dd, q, timestamp ):
    upload_scale = params.upload_scale
    simage = cv2.resize( image, None, None, upload_scale, upload_scale )

    process = {}
    process['token'] = params.process_token
    process['id'] = params.id_token
    process['image_scale'] = float(upload_scale)
    process['compliments'] = {}

    response = nr_api.process(simage, process)

    response = json.loads( response.content )
    reference = response['reference']

    #print( reference )

    time.sleep(0.5)

    results = nr_api.results( reference )

    if results.status_code == 200 :
        meta = json.loads(results.content)

        print( meta )

        if meta['status'] == 'OK' :
            image = dd.draw(image,meta.get('results',{}), use_image=True)

        data = {}
        data["image"] = image
        data["timestamp"] = timestamp
        q.put(data)

if __name__=="__main__" :
    if os.path.exists('config.local.yml') :
        params = Params('config.local.yml')
    else :
        params = Params('config.yml')

    interval = 1.0 / params.fps
    start_time = time.time()
    diff_time = 0

    cap = cv2.VideoCapture(0)
    assert cap.isOpened()

    nf = 0
    t0 = time.time()
    queue = Queue()

    dd = drawer( params.upload_scale )
    last_timestamp = -1

    while True :
        ret, frame = cap.read()
        if ret :
            current_time = time.time()
            if current_time - start_time + diff_time >= interval :
                diff_time = max( [ current_time - start_time - interval, 0.0 ] )
                start_time = current_time
                
                #nf += 1
                #print( nf / ( time.time() - t0 ) )

                t = threading.Thread( target=process_image, args=( frame, params, dd, queue, time.time() ) )
                t.start()

            if not queue.empty() :
                data = queue.get()

                if data["timestamp"] > last_timestamp :
                    cv2.imshow("Image", data['image'])
                    cv2.waitKey(1)
                    last_timestamp = data["timestamp"]
        else :
            break
