# nr-python-client

## Installation

- You need to use python 3
- Install the requirements

    pip install -r requirements.txt

- Register a stream on https://api.neuralrefinery.com and design a processing schema. Copy the 
stream token from the website and place it in the file config.yml. In this file you can also provide 
a id_token which can be any string. the use of id_token is to distinguish different video streams 
that use the same process token.

- Enter the credintials for https://api.neuralrefinery.com in the file auth.yml

- Run :
    python webcam.py


## Notes

- Try not to run each video stream with at most 10 frames per second (can be set in config.yml)
- This repository is being actively developed and how you will use the code can drastically change 
in the future updates