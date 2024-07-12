from queue import Queue,Empty
from typing import Dict
import time
import os
import pulsar
import threading
import json
from ApiMessageProcessor import ApiMessageProcessor
import Event
from kubernetes import client,config

nodeType : str = "api";
pulsarURL : str = "pulsar://localhost:6650";
topicName : str = "model-gpt-3.5-turbo";
maxProcessNum : int = 10;
apiURL : str = "https://api.openai-hk.com/v1/chat/completions";
apiKey : str = "hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c";
queue : Queue = Queue();
map : Dict = dict();
model : str = 'gpt-3.5-turbo'
serviceTopicName : str = '' 
debug : bool = False
pulsarToken : str = ''
AIModelNamespace : str = ''
AIModelName : str = ''
apiInstance = None
stopEvent = threading.Event()
startTime = 0

def init():
    global nodeType,pulsarURL,serviceTopicName,pulsarToken,topicName
    global maxProcessNum,apiURL,apiKey,queue,map,model,debug,AIModelName,AIModelNamespace
    nodeType = os.getenv('NODE_TYPE','api');
    pulsarURL = os.getenv('PULSAR_URL',"pulsar://localhost:6650");
    maxProcessNum = int(os.getenv('MAX_PROCESS_NUM','128'));
    apiURL = os.getenv('API_URL',"https://api.openai-hk.com/v1/chat/completions");
    apiKey = os.getenv('API_KEY',"hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c");
    model = os.getenv('MODEL_NAME','gpt-3.5-turbo')
    serviceTopicName = os.getenv('RES_TOPIC_NAME','res-topic')
    debug = bool(os.getenv('DEBUG','false'))
    pulsarToken = os.getenv('PULSAR_TOKEN','')
    AIModelName = os.getenv('AIMODEL_NAME','none')
    AIModelNamespace = os.getenv('AIMODEL_NAMESPACE','none')
    topicName = 'model-' + model
    queue = Queue();
    map = dict();

def createConsumer(url):
    global pulsarClient
    pulsarClient = pulsar.Client(
        service_url=url,
        operation_timeout_seconds=10,
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
        while True:
            msg = None
            if stopEvent.is_set() and time.time() > startTime:
                stopEvent.clear()
                global startTime
                startTime = 0
            elif stopEvent.is_set():
                time.sleep(5)
                continue
            try:
                msg = queue.get(True)
                print('{} take message: {}'.format(self.name,msg.data())) #debug
                amp = ApiMessageProcessor(msg,apiURL,apiKey,model)
                result = amp.process()
                self.sendResult(result)
                self.consumer.acknowledge(msg)
            except Empty:
                continue
            except json.JSONDecodeError as e:
                Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'GeneralError','Error decoding JSON')
                if msg:
                    self.consumer.negative_acknowledge(msg)
            except Exception as e:
                if e.args[0] == 'Http request failed,status code: 428':
                    Event.createEvent(apiInstance,AIModelName,AIModelNamespace,'AuthenticationError','The key is wrong!')
                elif e.args[0] == 'Http request failed,status code: 429':
                    if not stopEvent.is_set():
                        stopEvent.set()
                        global startTime
                        startTime = time.time() + 60
                else:
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
        config.load_kube_config()
    global apiInstance
    apiInstance = client.CoreV1Api()
    
if __name__ == '__main__':
    kubenetesInit()
    init()
    run()