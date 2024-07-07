package com.mycompany.app;

import org.apache.pulsar.client.api.Consumer;
import org.apache.pulsar.client.api.Message;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.PulsarClient;

/**
 * Hello world!
 *
 */
public class WokerNode
{
    // 参数
    String nodeType;
    String adminAdress;
    public static void main( String[] args ) throws Exception
    {
        PulsarClient client = PulsarClient.builder()
        .serviceUrl("pulsar://localhost:6650")
        .build();
        Producer<byte[]> producer = client.newProducer()
        .topic("my-topic")
        .create();

        producer.send("this is a message from java".getBytes());

        Consumer<byte[]> consumer = client.newConsumer()
        .topic("my-topic")
        .subscriptionName("my-subscription")
        .subscribe();

        while (true) {
            // Wait for a message
            Message<byte[]> msg = consumer.receive();
          
            try {
                // Do something with the message
                System.out.println("Message received: " + new String(msg.getData()));
          
                // Acknowledge the message
                consumer.acknowledge(msg);
            } catch (Exception e) {
                // Message failed to process, redeliver later
                consumer.negativeAcknowledge(msg);
            }
          }
        // consumer.close();
        // producer.close();
        // client.close();
    }
}
