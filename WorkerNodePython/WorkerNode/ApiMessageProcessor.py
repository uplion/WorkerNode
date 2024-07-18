import json
import requests
from sseclient import SSEClient
import websocket
import tiktoken


class ApiMessageProcessor:
    def __init__(self,msg,apiURL,apiKey,model,errorMode,errorData):
        self.msg = msg
        self.apiURL = apiURL
        self.apiKey = apiKey
        self.encoding = tiktoken.encoding_for_model(model)
        self.destination = None
        self.errorMode = errorMode
        self.errorData = errorData
    def process(self):
        jsonMsg = json.loads(self.msg.data().decode('utf-8'))
        requestID = jsonMsg['request_id']
        endPoint = jsonMsg['endpoint']
        stream = jsonMsg['stream']
        data = jsonMsg['data']
        print(f"{self.apiURL=} {stream=} {endPoint=} {requestID=}")
        try:
            if(stream == False):
                self.destination = endPoint
                if self.errorMode:
                    self.sendError(self.destination,requestID,self.errorData)
                    return None
                response = self.sendHttpRequest(data)
                print('received response: {}'.format(response))
                self.sendHttpResponse(response,requestID,endPoint)
                usage = {
                    "prompt_tokens": int(response['usage']['prompt_tokens']),
                    "completion_tokens": int(response['usage']['completion_tokens']),
                    "total_tokens": int(response['usage']['total_tokens'])
                }
                result = {
                    "request_id": requestID,
                    "usage": usage
                }
                return result
            else:
                ws = websocket.create_connection(endPoint.replace('http://','ws://'))
                self.destination = ws
                if self.errorMode:
                    self.sendError(self.destination,requestID,self.errorData)
                    return None
                tokens = self.sendStreamRequest(data,requestID,ws)
                usage = {
                    "prompt_tokens": tokens[0],
                    "completion_tokens": tokens[1],
                    "total_tokens": tokens[2]
                }
                result = {
                    "request_id": requestID,
                    "usage": usage
                }
                return result
        
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json()   
            self.sendError(self.destination,requestID,error_detail)
            raise e
        except Exception as e:
            raise e

    def sendHttpRequest(self,data):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.apiKey)
        }


        response = requests.post(self.apiURL,data=json.dumps(data),headers=headers)
        response.raise_for_status()
        return response.json()
    
    def sendHttpResponse(self,response,request_id,endpoint):
        headers = {
            'Content-Type' : 'application/json'
        }
        newResponse = {
            'request_id' : request_id,
            'data' : response
        }
        requests.post(endpoint,data=json.dumps(newResponse),headers=headers,verify=False)

    def sendStreamRequest(self,data,request_id,ws):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.apiKey)
        }

        def event_stream():
            for chunk in response.iter_content(chunk_size=None):
                yield chunk
        client = SSEClient(event_stream())

        response = requests.post(self.apiURL,data=json.dumps(data),headers=headers,verify=False)

        if response.status_code >= 400:
            e = requests.exceptions.HTTPError()
            e.response = response
            raise e
        

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        for message in data['messages']:
            if message['role'] == 'user':
                prompt_tokens = len(self.encoding.encode(message['content']))
                break;

        for event in client.events():
            if event.data == '[DONE]':
                self.sendStreamResponse(None,True,request_id,ws)
                ws.close()
                break
            if event.data:
                try:
                    event_data = json.loads(event.data)
                    print("received event: {}".format(event_data))
                    if 'choices' in event_data:
                        for choice in event_data['choices']:
                            if 'delta' in choice and 'content' in choice['delta']:
                                completion_tokens += len(self.encoding.encode(choice['delta']['content']))
                    self.sendStreamResponse(event_data,False,request_id,ws)
                except Exception as e:
                    raise e
        
        total_tokens = prompt_tokens + completion_tokens
        return (prompt_tokens,completion_tokens,total_tokens)
        

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
    
    def sendError(self,destination,request_id,error):
        if isinstance(destination,str):
            headers = {
                'Content-Type' : 'application/json'
            }
            newResponse = {
                'request_id' : request_id,
                'data' : error
            }
            requests.post(destination,data=json.dumps(newResponse),headers=headers,verify=False)
            print('send error: ' + json.dumps(newResponse))
        elif isinstance(destination,websocket.WebSocket):
            newResponse = {
                'request_id': request_id,
                'end': True,
                'data': error
            }
            responseString = json.dumps(newResponse)
            print('Send error: ' + responseString)
            destination.send(responseString)
        else :
            raise Exception('the type of endpoint is wrong!')
