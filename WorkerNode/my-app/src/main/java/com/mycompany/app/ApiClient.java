package com.mycompany.app;

// 这个文件是测试用的 没啥价值 qaq

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

// hello
public class ApiClient {

    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        ObjectMapper mapper = new ObjectMapper();

        // 创建请求体
        ObjectNode requestBody = mapper.createObjectNode();
        requestBody.put("model", "gpt-3.5-turbo-1106");
        requestBody.putArray("messages")
                   .add(mapper.createObjectNode()
                              .put("role", "user")
                              .put("content", "Hello, how are you?"));

        // 创建HTTP请求
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://api.openai-hk.com/v1/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + "hk-j9e9al1000037138f0cd6a31058a83dbb7a63f56fd48788c")
                .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
                .build();

        // 发送请求并获取响应
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // 解析JSON响应
        ObjectNode jsonResponse = (ObjectNode) mapper.readTree(response.body());

        // 打印响应
        System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(jsonResponse));
    }
}

