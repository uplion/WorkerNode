package com.mycompany.app;

import java.io.IOException;

import org.apache.pulsar.client.api.Consumer;
import org.apache.pulsar.client.api.Message;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.PulsarClient;
import org.apache.pulsar.client.api.PulsarClientException;
import org.apache.pulsar.client.api.SubscriptionType;

// 工作节点
public class WokerNode
{
    // 参数
    static String nodeType;
    static String adminAdress;
    static String pulsarURL;
    static String topicName;
    static String subscriptionName;
    static int maxProcessNum;

    // 手动初始化 测试用
    static void initForTest()
    {
        nodeType = "Api";
        adminAdress = "";
        pulsarURL = "pulsar://localhost:6650";
        topicName = "my-topic";
        subscriptionName = "my-subscription";
    }

    // 从环境变量读取初始化
    void init()
    {

    }

    // 运行
    public static void main( String[] args ) throws Exception
    {
        WokerNode.initForTest();
        // 创建 pulsar 客户端
        PulsarClient client = PulsarClient.builder()
        .serviceUrl(pulsarURL)
        .build();
        
        // 创建消息
        Producer<byte[]> producer = client.newProducer()
        .topic(topicName)
        .create();
        producer.send("this is a message from java".getBytes());

        // 创建消费者接收消息
        myConsumer[] test = new myConsumer[maxProcessNum];
        for(int i=0;i<maxProcessNum;i++)
        {
            test[i] = new myConsumer(topicName, subscriptionName,nodeType);
            test[i].start(client, "Thread " + String.valueOf(i));
        }
    }
}

// Api 类型工作节点
class ApiWokerNode extends WokerNode
{
    // 参数
    String apiKey;
    String apiURL;

    ApiWokerNode(String url)
    {
        apiURL = new String(url);
    }

    void init()
    {
        nodeType = "api";
        adminAdress = "";
        pulsarURL = "pulsar://localhost:6650";
        apiKey = "hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c";
        apiURL = "https://api.openai-hk.com/v1/chat/completions";
        maxProcessNum = 10;
    } 

}

// 消费者，接收并处理消息
class myConsumer implements Runnable
{
    // 参数
    String topic;
    String subscribeName;
    Consumer<byte []> consumer;
    Thread th;
    String nodeType;
    
    // 构造函数
    myConsumer(String topic,String subscribeName,String nodeType)
    {
        this.topic = new String(topic);
        this.subscribeName = new String(subscribeName);
        this.nodeType = new String(nodeType);
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
                Message<byte []> msg = consumer.receive();
                try
                {
                    // 处理消息

                    // 如果是 Api 节点
                    if(nodeType.equals("Api"))
                    {
                        ApiMessageProcessor mp = new ApiMessageProcessor();
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
                    System.out.println("received message: " + new String(msg.getData()));
                    consumer.acknowledge(msg);
                }
                // 处理失败 返回 NAK
                catch (Exception e)
                {
                    consumer.negativeAcknowledge(msg);
                }
            }
        }
        // 客户端失败
        catch(PulsarClientException e)
        {
            e.printStackTrace();
        }
        // 其他异常
        catch(Exception e)
        {
            e.printStackTrace();
        }
    }

    // 启动线程
    void start(PulsarClient client,String name) throws Exception
    {
        if(th == null)
        {
            this.consumer = client.newConsumer().topic(this.topic)
            .subscriptionName(this.subscribeName)
            .subscriptionType(SubscriptionType.Shared)
            .subscribe();
            th = new Thread(this,name);
            th.start();
        }
    }
}
