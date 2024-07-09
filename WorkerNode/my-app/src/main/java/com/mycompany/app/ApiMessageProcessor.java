package com.mycompany.app;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import org.apache.pulsar.client.api.Message;
import org.apache.pulsar.client.api.Producer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import java.util.Map;

// Api 消息处理器
public class ApiMessageProcessor
{
    String apiURL;
    String apiKey;
    String requestID;
    Boolean stream;
    String endPoint;
    JsonNode dataNode;
    Boolean debug;
    Producer<byte []> producer;
    Map<String,WebSocketClient> map;

    ApiMessageProcessor(String url,String key,Producer<byte []> producer,Map<String,WebSocketClient> map)
    {
        this.apiURL = new String(url);
        this.apiKey = new String(key);
        this.producer = producer;
        this.map = map;
        stream = false;
    }

    void process(Message<byte []> msg) throws Exception
    {
        // 转换成 JsonNode
        ObjectMapper objectMapper = new ObjectMapper();
        InputStream inputStream = new ByteArrayInputStream(msg.getData());
        JsonNode rootNode = objectMapper.readTree(inputStream);

        // 处理请求
        requestID = rootNode.get("request_id").asText();
        stream = rootNode.get("stream").asBoolean();
        endPoint = rootNode.get("endpoint").asText();
        dataNode = rootNode.get("data");

        // 处理聊天请求
        sendRequest(dataNode);
    }

    void sendRequest(JsonNode dataNode) throws Exception
    {
        HttpClient client = HttpClient.newHttpClient();
        ObjectMapper mapper = new ObjectMapper();

        // 创建请求体
        ObjectNode requestBody = mapper.createObjectNode();
        requestBody.put("model",dataNode.get("model").asText());
        requestBody.set("messages", dataNode.get("messages"));
    
        // 创建 Http 请求
        HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(apiURL))
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + apiKey)
        .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
        .build();

        // 发送请求
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // 解析 JSON 响应并添加 request_id
        ObjectNode jsonResponse = (ObjectNode) mapper.readTree(response.body());
        ObjectNode newResponse = mapper.createObjectNode();
        newResponse.set("data",jsonResponse);
        newResponse.put("request_id", requestID);
        

        if(stream == false)
        {   
            // 转换成 String
            String jsonString = mapper.writeValueAsString(newResponse);
            
            // 发送响应
            sendResponse(jsonString);

            // debug 打印相关信息
            System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(jsonResponse));
            
        }
        else
        {
            // TODO: stream 为 true 时需要建立 websocket 返回结果
            // end = true 表明响应结束
            jsonResponse.put("end","true");

            if(map.containsKey(endPoint))
            {
                
            }
        }
    }

    void sendResponse(String responseString) throws Exception
    {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(endPoint))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(responseString))
                .build();

        HttpResponse<String> response = client.send(request,HttpResponse.BodyHandlers.ofString());
    }
}
