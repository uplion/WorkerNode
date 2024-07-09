package com.mycompany.app;

import java.net.URI;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import javax.websocket.*;

@ClientEndpoint
public class WebSocketClient 
{
    private Session session;
    private static CountDownLatch latch;

    @OnOpen
    public void onOpen(Session session)
    {
        System.out.println("connected to endpoint: " + session.getBasicRemote()); // debug
        this.session = session;
        latch.countDown();
    }

    @OnMessage
    public void processMessage(String message)
    {
        System.out.println("received message:" + message); // debug
    }

    @OnError
    public void processError(Throwable t)
    {
        t.printStackTrace();
    }

    public void sendMessage(String message)
    {
        try
        {
            this.session.getBasicRemote().sendText(message);
        }
        catch(Exception e)
        {
            e.printStackTrace();
        }
    }

    public void run(String uri) throws Exception
    {
        latch = new CountDownLatch(1);

        WebSocketContainer container = ContainerProvider.getWebSocketContainer();
        WebSocketClient client = new WebSocketClient();

        container.connectToServer(client, new URI(uri));

        latch.await(5, TimeUnit.SECONDS);

        while(true)
        {
            Thread.sleep(1000);
        }
    }
}
