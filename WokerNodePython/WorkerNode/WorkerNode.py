from queue import Queue
from typing import Dict
import os
import pulsar
import threading
from ApiMessageProcessor import ApiMessageProcessor

nodeType : str = "Api";
adminAddress : str = "";
pulsarURL : str = "pulsar://localhost:6650";
topicName : str = "model-gpt-3.5-turbo";
subscriptionName : str = "my-subscription";
maxProcessNum : int = 10;
apiURL : str = "https://api.openai-hk.com/v1/chat/completions";
apiKey : str = "hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c";
queue : Queue = Queue();
map : Dict = dict();

def init():
    global nodeType,adminAddress,pulsarURL,topicName,subscriptionName
    global maxProcessNum,apiURL,apiKey,queue,map
    nodeType = os.getenv('NODETYPE','Api');
    adminAddress = os.getenv('ADMIN_ADRESS','');
    pulsarURL = os.getenv('PULSAR_URL',"pulsar://localhost:6650");
    topicName = os.getenv("TOPIC_NAME","model-gpt-3.5-turbo");
    subscriptionName = os.getenv('SUBSCRIPTION_NAME',"my-subscription");
    maxProcessNum = int(os.getenv('MAX_PROCESS_NUM','10'));
    apiURL = os.getenv('API_URL',"https://api.openai-hk.com/v1/chat/completions");
    apiKey = os.getenv('API_KEY',"hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c");
    queue = Queue();
    map = dict();

def run():
    client = pulsar.Client(pulsarURL)

    consumer = client.subscribe(topicName,subscriptionName)

    producer = client.create_producer(topicName)

    # producer.send('this is a message from python!'.encode('utf-8')) # debug

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
                # TODO: 处理消息
                amp = ApiMessageProcessor(msg,apiURL,apiKey)
                amp.process()
                self.consumer.acknowledge(msg)
            except Queue.empty:
                continue
            except Exception as e:
                print("erroe message: {e}")
                self.consumer.negative_acknowledge(msg) # type: ignore

if __name__ == '__main__':
    run()