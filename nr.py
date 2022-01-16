import yaml
import cv2
import json
import requests

class Params :
    def __init__( self, config_file ):
        self.params = yaml.safe_load(open(config_file).read())

    def __getattr__( self, item ):
        return self.params.get(item, None)

class auth :
    def __init__( self ):
        auth = Params('auth.yml')

        self._auth = {}
        self._auth['username'] = auth.username
        self._auth['password'] = auth.password
        self._auth['token'] = ""
        self._server = auth.server

    def _get_token( self ):
        data = {}
        data["username"] = self._auth['username']
        data["password"] = self._auth['password']

        response = requests.post( '%s/api/token-auth/' % ( self._server ), data=data )

        if response.status_code == 200 :
            content = json.loads( response.content.decode() )
            self._auth['token'] = content['access']
        else :
            print('Could not fetch a token')

    def _send_request( self, url, data, headers={} ):
        response = None

        done = False
        while not done :
            try :
                headers['Authorization'] = 'Bearer %s' % ( self._auth['token'] )

                response = requests.post( url, data=data, headers=headers )

                assert response.status_code != 401, "Unauthorized"
                done = True
            except :
                self._get_token()

        return response


class api( auth ) :
    def __init__( self ):
        super().__init__()
        #self._auth = Params('auth.yml')

    def process( self, image, process ):
        ret, encoded = cv2.imencode( '.jpg', image )
        encoded = encoded.tobytes()

        headers = {}
        headers['Stream-Token'] = json.dumps( process )
        headers['Content-Type'] = 'image/jpeg'

        return self._send_request( '%s/api/process/' % ( self._server ), 
                                   data=encoded, 
                                   headers=headers )

    def results( self, reference ):
        headers = {}
        headers['Reference'] = reference

        return self._send_request( '%s/api/results/' % ( self._server ), 
                                   data="", 
                                   headers=headers )
