import json
import requests
from sseclient import SSEClient

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
                # TODO: 流式响应
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

        for event in client.events():
            if event.data == '[DONE]':
                self.sendStreamResponse(None,True,request_id,endpoint)
                break
            if event.data:
                try:
                    event_data = json.loads(event.data)
                    print("received event: {}".format(event_data))
                    self.sendStreamResponse(event_data,False,request_id,endpoint)
                except json.JSONDecodeError:
                    print("can handle event data: {}".format(event.data))
        

    def sendStreamResponse(self,response,end,request_id,endpoint):
        headers = {
            'Content-Type' : 'applicatiion/json'
        }
        if end == True:
            newResponse = {
                'request_id': request_id,
                'end': 'true'
        }
        else:
            newResponse = {
                'request_id': request_id,
                'end': 'false',
                'data': response
            }
        requests.post(endpoint,data=json.dumps(newResponse),headers=headers)