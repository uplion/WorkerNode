package com.mycompany.app;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import org.apache.pulsar.client.api.Message;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

// Api 消息处理器
public class ApiMessageProcessor
{
    String requestID;
    Boolean stream;
    String endPoint;
    JsonNode dataNode;
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
        dataNode = rootNode.get("data");

        // 处理聊天请求
        sendRuquest(dataNode);
    }

    void sendRuquest(JsonNode dataNode)
    {

    }
}
