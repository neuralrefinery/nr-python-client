import numpy as np
import nr
import time
import requests

token = "UIQuSAlwLfuslapMyEWo"

if __name__=="__main__" :
    
    while True :
        headers = {}
        headers["Token"] = token

        response = requests.get( 'https://api.neuralrefinery.com/api/last-ref-results/', headers=headers )

        print( response )
        print( response.content )


        time.sleep(1.0)
