from queue import Queue
from typing import Dict
import os

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