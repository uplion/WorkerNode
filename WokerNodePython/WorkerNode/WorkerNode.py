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
from kubernetes import client,config

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
AIModelNamespace : str = ''
AIModelName : str = ''
apiInstance = None
stopEvent = threading.Event()
startTime = 0
sockets = dict()

def init():
    global nodeType,pulsarURL,serviceTopicName,pulsarToken,topicName
    global maxProcessNum,apiURL,apiKey,queue,map,model,debug,AIModelName,AIModelNamespace
    nodeType = os.getenv('NODE_TYPE','local');
    pulsarURL = os.getenv('PULSAR_URL',"pulsar://localhost:6650");
    maxProcessNum = int(os.getenv('MAX_PROCESS_NUM','128'));
    apiURL = os.getenv('API_URL',"http://localhost:8080/v1/chat/completions");
    apiKey = os.getenv('API_KEY',"sk-no-key-required");
    model = os.getenv('MODEL_NAME','gpt-3.5-turbo')
    serviceTopicName = os.getenv('RES_TOPIC_NAME','res-topic')
    debug = bool(os.getenv('DEBUG','false'))
    pulsarToken = os.getenv('PULSAR_TOKEN','')
    AIModelName = os.getenv('AIMODEL_NAME','none')
    AIModelNamespace = os.getenv('AIMODEL_NAMESPACE','none')
    topicName = 'model-' + model
    queue = Queue();
    map = dict();

def localInit():
    currentDir = os.getcwd()
    shFile = 'local.sh'
    fullPath = os.path.join(currentDir,shFile)
    try:
        subprocess.run(['bash',fullPath],check=True)
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
    if nodeType == 'local':
        localInit()

    global pulsarClient,consumer

    pulsarClient,consumer = createConsumer(pulsarURL)
    
    processors = list()

    for i in range(maxProcessNum):
        processor = Processor('Thread-' + str(i),consumer)
        processor.start()
        processors.append(processor)

    try:
        while True:
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
        global startTime
        while True:
            msg = None
            if stopEvent.is_set() and time.time() > startTime:
                stopEvent.clear()
                startTime = 0
            elif stopEvent.is_set():
                time.sleep(5)
                continue
            try:
                msg = queue.get(True)
                print('{} take message: {}'.format(self.name,msg.data())) #debug
                if nodeType == 'api':
                    amp = ApiMessageProcessor(msg,apiURL,apiKey,model)
                else:
                    amp = ApiMessageProcessor(msg,apiURL,apiKey,'gpt-3.5-turbo')
                result = amp.process()
                self.sendResult(result)
                self.consumer.acknowledge(msg)
            except Empty:
                continue
            except json.JSONDecodeError as e:
                Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'GeneralError','Error decoding JSON')
                if msg:
                    self.consumer.negative_acknowledge(msg)
            except requests.exceptions.HTTPError as e:
                # 处理 HTTP 错误
                if e.response.status_code == 401:
                    error_detail = e.response.json()
                    Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'AuthenticationError',json.dumps(error_detail))
                elif e.response.status_code == 429:
                    error_detail = e.response.json()
                    if 'Rate limit reached for requests' in error_detail['error']['message']:
                        if not stopEvent.isSet():
                            stopEvent.set()
                            startTime = time.time() + 60
                    else:
                        Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'APIQuotaExceededError',json.dumps(error_detail))
                else:
                    error_detail = e.response.json()
                    Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'GeneralError',json.dumps(error_detail))
                if msg:
                    self.consumer.negative_acknowledge(msg)

            except Exception as e:
                Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'GeneralError',e.__str__())
                if msg:
                    self.consumer.negative_acknowledge(msg)

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
        except:
            return
    global apiInstance
    apiInstance = client.CoreV1Api()
    
if __name__ == '__main__':
    kubenetesInit()
    init()
    run()