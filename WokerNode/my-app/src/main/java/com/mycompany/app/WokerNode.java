package com.mycompany.app;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import org.apache.pulsar.client.api.Consumer;
import org.apache.pulsar.client.api.Message;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.PulsarClient;
import org.apache.pulsar.client.api.PulsarClientException;
import org.apache.pulsar.client.api.SubscriptionType;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;


/**
 * Hello world!
 *
 */
public class WokerNode
{
    // 参数
    String nodeType;
    String adminAdress;
    String pulsarURL;
    String apiKey;
    String apiURL;
    int maxProcessNum = 10;

    void init()
    {
        nodeType = "api";
        adminAdress = "";
        pulsarURL = "pulsar://localhost:6650";
        apiKey = "";
        apiURL = "";
    } 

    public static void main( String[] args ) throws Exception
    {
        PulsarClient client = PulsarClient.builder()
        .serviceUrl("pulsar://localhost:6650")
        .build();
        Producer<byte[]> producer = client.newProducer()
        .topic("my-topic")
        .create();

        producer.send("this is a message from java".getBytes());

        myConsumer test = new myConsumer("my-topic", "my-subscription");
        test.start(client, "Thread 1");
    }
}

class myConsumer implements Runnable
{
    String topic;
    String subscribeName;
    Consumer<byte []> consumer;
    MessageProcessor mp;
    Thread th;
    myConsumer(String topic,String subscribeName)
    {
        this.topic = new String(topic);
        this.subscribeName = new String(subscribeName);
    }

    @Override
    public void run()
    {
        try
        {
            while(true)
            {
                Message<byte []> msg = consumer.receive();
                try
                {
                    mp.process(msg);
                    System.out.println("received message: " + new String(msg.getData()));
                    consumer.acknowledge(msg);
                }
                catch (Exception e)
                {
                    consumer.negativeAcknowledge(msg);
                }
            }
        }
        catch(PulsarClientException e)
        {
            e.printStackTrace();
        }
    }

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

class MessageProcessor
{
    String requestID;
    Boolean stream;
    String endPoint;
    String data;
    void process(Message<byte []> msg) throws Exception
    {
        // 转换成 JsonNode
        ObjectMapper objectMapper = new ObjectMapper();
        InputStream inputStream = new ByteArrayInputStream(msg.getData());
        JsonNode rootNode = objectMapper.readTree(inputStream);

        // 处理请求
        requestID = rootNode.get("request_id").asText();
        stream = rootNode.get("stream").asBoolean();
        endPoint = rootNode.get("endPoint").asText();
        data = rootNode.get("data").asText();

        // 处理聊天请求
        sendRuquest(data);
    }

    void sendRuquest(String data)
    {

    }
}