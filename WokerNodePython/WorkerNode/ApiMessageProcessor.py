import json
import requests

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
                if(response == None):
                    raise Exception('Request failed!')
                else:
                    print('received response: {}'.format(response))
                    self.sendHttpResponse(response,requestID,endPoint)
            else:
                # TODO: 流式响应
                print('stream = true')
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
            print("Http request failed,status code: {}".format(response.status_code))
            return None
    
    def sendHttpResponse(self,response,request_id,endpoint):
        headers = {
            'Content-Type' : 'application/json'
        }
        newResponse = {
            'request_id' : request_id,
            'data' : response
        }
        requests.post(endpoint,data=json.dumps(newResponse),headers=headers)
