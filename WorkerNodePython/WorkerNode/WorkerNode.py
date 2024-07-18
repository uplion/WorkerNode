from queue import Queue,Empty
from typing import Dict
import time
import os
import pulsar
import threading
import json
from ApiMessageProcessor import ApiMessageProcessor
import Event
import requests
import subprocess
from tqdm import tqdm
from urllib.parse import urlparse
from kubernetes import client,config
from dotenv import load_dotenv

load_dotenv()

nodeType : str = '';
pulsarURL : str = '';
topicName : str = '';
maxProcessNum : int = 0;
apiURL : str = '';
apiKey : str = '';
queue : Queue = Queue();
map : Dict = dict();
model : str = ''
serviceTopicName : str = '' 
debug : bool = False
pulsarToken : str = ''
AIModelNamespace = os.getenv('AIMODEL_NAMESPACE')
AIModelName = os.getenv('AIMODEL_NAME')
apiInstance = None
stopEvent = threading.Event()
startTime = 0
sockets = dict()
condition = threading.Condition()
activeThreads = 0
errorMode = False
errorData = dict()

def getenv(key, defaultValue = None):
    e = os.getenv(key)
    if not e:
        if defaultValue != None:
            return defaultValue
        print(f"Missing env var: {key}")
        Event.createEvent(apiInstance,AIModelNamespace,AIModelName,"ConfigurationError",f"Missing env var: {key}")
        exit(1)
    return e

def wget_like_download(url, output_path=None):
    try:
        head_response = requests.head(url, allow_redirects=True)
        head_response.raise_for_status()
        
        if not output_path:
            filename = urlparse(head_response.url).path.split('/')[-1]
            if not filename:
                filename = 'downloaded_file'
        else:
            filename = output_path
        
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        if os.path.exists(filename):
            print(f"File '{filename}' already exists. Skipping download.")
            return
        
        with open(filename, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(chunk_size=8192):
                size = file.write(data)
                progress_bar.update(size)
        
        print(f"File downloaded successfully as {filename}")
    
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")

def init():
    global nodeType,pulsarURL,serviceTopicName,pulsarToken,topicName
    global maxProcessNum,apiURL,apiKey,queue,map,model,debug,AIModelName,AIModelNamespace
    nodeType = getenv('NODE_TYPE');
    pulsarURL = getenv('PULSAR_URL');
    maxProcessNum = int(getenv('MAX_PROCESS_NUM', '128'));
    if nodeType == 'local':
        apiURL = 'http://localhost:8080/v1/chat/completions'
        apiKey = 'sk-no-key-required'
    else:
        apiURL = getenv('API_URL') + "/chat/completions";
        apiKey = getenv('API_KEY');
    model = getenv('MODEL_NAME')
    serviceTopicName = getenv('RES_TOPIC_NAME')
    debug = getenv('DEBUG', 'false') == 'true'
    pulsarToken = getenv('PULSAR_TOKEN', '')
    topicName = 'model-' + model
    queue = Queue();
    map = dict();

def localInit():
    currentDir = os.getcwd()
    shFile = 'local.sh'
    fullPath = os.path.join(currentDir,shFile)
    try:
        wget_like_download(
            "https://huggingface.co/Mozilla/TinyLlama-1.1B-Chat-v1.0-llamafile/resolve/main/TinyLlama-1.1B-Chat-v1.0.F16.llamafile?download=true",
            "TinyLlama-1.1B-Chat-v1.0-llamafile"
        )
        subprocess.Popen(['bash', 'local.sh'],stdout=subprocess.PIPE)
    except Exception as e:
        raise e

def createConsumer(url):
    global pulsarClient
    pulsarClient = pulsar.Client(
        service_url=url,
        authentication=pulsar.AuthenticationToken(pulsarToken),
        operation_timeout_seconds=60,
        )

    try:
        global consumer
        consumer = pulsarClient.subscribe(
            topic=topicName,
            subscription_name=topicName + '-subscription',
            consumer_type=pulsar.ConsumerType.Shared
            )
        return pulsarClient,consumer
    except Exception as e:
        Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'MessageQueueConnectionError',e.__str__())
        exit(1)

def run():
    global queue,errorMode,errorData
    if nodeType == 'local':
        if not model == 'TinyLlama-1.1B':
            errorMode = True
            errorData = {
                "error": {
                    "message": "The model \'{}\' does not exist or you do not have access to it.".format(model),
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "model_not_found"
                }
            }
            Event.createEvent(apiInstance,AIModelNamespace,AIModelName,'ConfigurationError','unspported model ' + model)
        else:
            localInit()

    global pulsarClient,consumer

    pulsarClient,consumer = createConsumer(pulsarURL)
    
    processors = []

    for i in range(maxProcessNum):
        processor = Processor('Thread-' + str(i),consumer)
        processor.start()
        processors.append(processor)

    try:
        while True:
            with condition:
                while activeThreads >= maxProcessNum:
                    condition.wait()
            msg = consumer.receive()
            print('received message: {}'.format(msg.data())) # debug
            queue.put(msg,True)
                
    except KeyboardInterrupt:
        print('Stopping consumer...')
    finally:
        consumer.close()
        pulsarClient.close()


class Processor(threading.Thread):
    def __init__(self,name,consumer):
        threading.Thread.__init__(self)
        self.name = name
        self.consumer = consumer
        self.producer = pulsarClient.create_producer(serviceTopicName)
    def run(self):
        global startTime,condition,activeThreads,queue,errorMode,errorData
        while True:
            msg = None
            if stopEvent.is_set() and time.time() > startTime:
                stopEvent.clear()
                startTime = 0
            elif stopEvent.is_set():
                time.sleep(5)
                continue
            msg = queue.get(True)
            with condition:
                activeThreads += 1
                
            try:
                print('{} take message: {}'.format(self.name,msg.data())) #debug
                if nodeType == 'api':
                    amp = ApiMessageProcessor(msg,apiURL,apiKey,model,errorMode,errorData)
                else:
                    amp = ApiMessageProcessor(msg,apiURL,apiKey,'gpt-3.5-turbo',errorMode,errorData)
                result = amp.process()
                if result != None:
                    self.sendResult(result)
                self.consumer.acknowledge(msg)
            except Empty:
                continue
            except json.JSONDecodeError as e:
                if msg:
                    self.consumer.acknowledge(msg)
            except requests.exceptions.HTTPError as e:
                # 处理 HTTP 错误
                if e.response.status_code == 401:
                    error_detail = e.response.json()
                    errorMode = True
                    errorData = error_detail
                    Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'AuthenticationError',error_detail['error']['message'])
                elif e.response.status_code == 429:
                    error_detail = e.response.json()
                    errorMode = True
                    errorData = error_detail
                    if 'Rate limit reached for requests' in error_detail['error']['message']:
                        if not stopEvent.isSet():
                            stopEvent.set()
                            startTime = time.time() + 60
                    else:
                        Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'APIQuotaExceededError',error_detail['error']['message'])
                elif e.response.status_code == 404:
                    error_detail = e.response.json()
                    errorMode = True
                    errorData = error_detail
                    if 'model' in error_detail['error']['message']:
                        Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'ConfigurationError',error_detail['error']['message'])
                    else:
                        Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'GeneralError',error_detail['error']['message'])
                else:
                    error_detail = e.response.json()
                    errorMode = True
                    errorData = error_detail
                    print('error status code: {}'.format(e.response.status_code))
                    Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'GeneralError',error_detail['error']['message'])
                if msg:
                    self.consumer.acknowledge(msg)
            

            finally:
                queue.task_done()
                with condition:
                    activeThreads -= 1
                    condition.notify()

    def sendResult(self,result):
        result['model'] = model
        result['ai_model_name'] = AIModelName
        result['ai_model_namespace'] = AIModelNamespace
        print('send result: ' + json.dumps(result))
        self.producer.send(json.dumps(result).encode('utf-8'))
        
                

def kubenetesInit():
    try:
        config.load_incluster_config()
    except:
        try:
            config.load_kube_config()
        except Exception as e:
            print(e)
            return
    global apiInstance
    apiInstance = client.CoreV1Api()
    
if __name__ == '__main__':
    if AIModelName:
        kubenetesInit()
    init()
    run()