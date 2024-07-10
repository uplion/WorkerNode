from queue import Queue
from typing import Dict
import os
import pulsar
import threading
from ApiMessageProcessor import ApiMessageProcessor
import Event

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
podNamespace : str = ''
podName : str = ''

def init():
    global nodeType,pulsarURL,serviceTopicName,pulsarToken,topicName
    global maxProcessNum,apiURL,apiKey,queue,map,model,debug,podName,podNamespace
    nodeType = os.getenv('NODETYPE','Api');
    pulsarURL = os.getenv('PULSAR_URL',"pulsar://localhost:6650");
    maxProcessNum = int(os.getenv('MAX_PROCESS_NUM','10'));
    apiURL = os.getenv('API_URL',"https://api.openai-hk.com/v1/chat/completions");
    apiKey = os.getenv('API_KEY',"hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c");
    model = os.getenv('MODEL_NAME','gpt-3.5-turbo')
    serviceTopicName = os.getenv('RES_TOPIC_NAME','')
    debug = bool(os.getenv('DEBUG','false'))
    pulsarToken = os.getenv('PULSAR_TOKEN','')
    podName = os.getenv('POD_NAME','')
    podNamespace = os.getenv('POD_NAMESPACE','')
    topicName = 'model-' + model
    queue = Queue();
    map = dict();

def run():
    client = pulsar.Client(pulsarURL)

    consumer = client.subscribe(topicName,topicName + '-subscription')

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
        client.close()


class Processor(threading.Thread):
    def __init__(self,name,consumer):
        threading.Thread.__init__(self)
        self.name = name
        self.consumer = consumer
    def run(self):
        while True:
            try:
                msg = queue.get(True)
                print('{} take message: {}'.format(self.name,msg.data())) #debug
                amp = ApiMessageProcessor(msg,apiURL,apiKey)
                amp.process()
                self.consumer.acknowledge(msg)
            except Queue.empty:
                continue
            except Exception as e:
                print("erroe message: {e}")
                self.consumer.negative_acknowledge(msg) # type: ignore

if __name__ == '__main__':
    init()
    run()