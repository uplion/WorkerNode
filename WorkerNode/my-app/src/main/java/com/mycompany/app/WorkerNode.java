package com.mycompany.app;

import java.io.IOException;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingDeque;

import org.apache.pulsar.client.api.Consumer;
import org.apache.pulsar.client.api.Message;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.PulsarClient;
import org.apache.pulsar.client.api.SubscriptionType;

// 工作节点
public class WorkerNode
{
    // 参数
    static String nodeType;
    static String apiURL;
    static String adminAddress;
    static String pulsarURL;
    static String pulsarToken;
    static String topicName;
    static String subscriptionName;
    static int maxProcessNum;
    static String apiKey;
    static Boolean debug;
    static String servicePulsarURL;
    static String servicePulsarToken;
    static BlockingQueue<Message <byte []>> queue;

    // 手动初始化 测试用
    static void initForTest()
    {
        nodeType = "Api";
        adminAddress = "";
        pulsarURL = "pulsar://localhost:6650";
        topicName = "my-topic";
        subscriptionName = "my-subscription";
        maxProcessNum = 10;
        apiURL = "https://api.openai-hk.com/v1/chat/completions";
        apiKey = "hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c";
        queue = new LinkedBlockingDeque<>();
    }

    // 从环境变量读取初始化
    void init()
    {
        
    }

    // 运行
    public static void main( String[] args ) throws Exception
    {
        WorkerNode.initForTest();
        // 创建 pulsar 客户端
        PulsarClient client = PulsarClient.builder()
        .serviceUrl(pulsarURL)
        .build();
        
        // 创建生产者生产消息
        Producer<byte[]> producer = client.newProducer()
        .topic(topicName)
        .create();
        producer.send("this is a message from java".getBytes());

        // 创建消费者接收消息
        Consumer<byte []> consumer = client.newConsumer().topic(topicName)
            .subscriptionName(subscriptionName)
            .subscriptionType(SubscriptionType.Shared)
            .subscribe();

        // 创建处理消息的处理器
        Processor[] processors = new Processor[maxProcessNum];
        for(int i=0;i<maxProcessNum;i++)
        {
            processors[i] = new Processor(nodeType, queue, consumer,apiURL,apiKey,producer);
            processors[i].start("Thread " + String.valueOf(i));
        }

        Thread.sleep(500);

        // 不断接收消息
        while(true)
        {
            Message<byte []> msg = consumer.receive();
            queue.put(msg);
        }
    }
}

// 消费者，接收并处理消息
class Processor implements Runnable
{
    // 参数
    Thread th;
    String nodeType;
    String apiURL;
    String apiKey;
    Producer<byte []> producer;
    BlockingQueue<Message <byte []>> queue;
    Consumer<byte []> consumer;
    
    // 构造函数
    Processor(String nodeType,BlockingQueue<Message <byte []>> queue,Consumer<byte []> consumer,String apiURL,String apiKey,Producer<byte []> producer)
    {
        this.nodeType = new String(nodeType);
        this.queue = queue;
        this.consumer = consumer;
        this.apiURL = new String(apiURL);
        this.apiKey = new String(apiKey);
        this.producer = producer;
    }

    // 线程的 run 方法
    @Override
    public void run()
    {
        try
        {
            while(true)
            {
                // 尝试获取消息
                Message<byte []> msg = queue.take();
                try
                {
                    // 处理消息

                    // 如果是 Api 节点
                    if(nodeType.equals("Api"))
                    {
                        ApiMessageProcessor mp = new ApiMessageProcessor(apiURL,apiKey,producer);
                        mp.process(msg);
                    }
                    else if(nodeType.equals("GPU"))
                    {
                        
                    }
                    else
                    {
                        throw new IOException("The nodeType is illegal!\n");
                    }
                    // 处理成功 返回 ACK
                    consumer.acknowledge(msg);
                }
                // 处理失败 返回 NAK
                catch (Exception e)
                {
                    consumer.negativeAcknowledge(msg);
                }
            }
        }
        // 其他异常
        catch(Exception e)
        {
            e.printStackTrace();
        }
    }

    // 启动线程
    void start(String name) throws Exception
    {
        if(th == null)
        {
            th = new Thread(this,name);
            th.start();
        }
    }
}
