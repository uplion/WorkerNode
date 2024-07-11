import json
import requests
from sseclient import SSEClient
import websocket

class ApiMessageProcessor:
    def __init__(self,msg,apiURL,apiKey):
        self.msg = msg
        self.apiURL = apiURL
        self.apiKey = apiKey
    def process(self):
        try:
            jsonMsg = json.loads(self.msg.data().decode('utf-8'))
            requestID = jsonMsg['request_id']
            endPoint = jsonMsg['endpoint']
            stream = jsonMsg['stream']
            data = jsonMsg['data']
            if(stream == False):
                response = self.sendHttpRequest(data)
                print('received response: {}'.format(response))
                self.sendHttpResponse(response,requestID,endPoint)
            else:
                self.sendStreamRequest(data,requestID,endPoint)
        except json.JSONDecodeError as e:
            print('Error decoding JSON: {}'.format(e))
        except Exception as e:
            print('Error message: {}'.format(e))

    def sendHttpRequest(self,data):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.apiKey)
        }

        response = requests.post(self.apiURL,data=json.dumps(data),headers=headers)

        if response.status_code == 200:
            jsonResponse = response.json()
            return jsonResponse
        else: 
            raise Exception("Http request failed,status code: {}".format(response.status_code))
    
    def sendHttpResponse(self,response,request_id,endpoint):
        headers = {
            'Content-Type' : 'application/json'
        }
        newResponse = {
            'request_id' : request_id,
            'data' : response
        }
        requests.post(endpoint,data=json.dumps(newResponse),headers=headers)

    def sendStreamRequest(self,data,request_id,endpoint):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.apiKey)
        }

        response = requests.post(self.apiURL,data=json.dumps(data),headers=headers)

        if response.status_code != 200:
            raise Exception("request failed, status code = {}".format(response.status_code))
        def event_stream():
            for chunk in response.iter_content(chunk_size=None):
                yield chunk
        client = SSEClient(event_stream())

        ws = websocket.create_connection(endpoint.replace('http://','ws://'))

        for event in client.events():
            if event.data == '[DONE]':
                self.sendStreamResponse(None,True,request_id,ws)
                ws.close()
                break
            if event.data:
                try:
                    event_data = json.loads(event.data)
                    print("received event: {}".format(event_data))
                    self.sendStreamResponse(event_data,False,request_id,ws)
                except json.JSONDecodeError:
                    print("can handle event data: {}".format(event.data))
        

    def sendStreamResponse(self,response,end,request_id,ws):
        if end == True:
            newResponse = {
                'request_id': request_id,
                'end': True
        }
        else:
            newResponse = {
                'request_id': request_id,
                'end': False,
                'data': response
            }
        responseString = json.dumps(newResponse)
        print('Send response: ' + responseString)
        ws.send(responseString)