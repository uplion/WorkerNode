package main

import (
	"context"
	"encoding/json"
	"github.com/apache/pulsar-client-go/pulsar"
	"log"
	"net/http"
	"os"
	"strings"
)

const MODEL_NAME = "static"

var PULSAR_URL string

func init() {
	if v, ok := os.LookupEnv("PULSAR_URL"); ok {
		PULSAR_URL = v
	} else {
		PULSAR_URL = "pulsar://localhost:6650"
	}
}

const STATIC_RESPONSE = `{
  "id": "chatcmpl-9l52qe9ecWkWTuMPAMbFD7fXNzDCA",
  "object": "chat.completion",
  "created": 1721007836,
  "model": "gpt-3.5-turbo-0125",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 9,
    "total_tokens": 18
  },
  "system_fingerprint": null
}`

type Task struct {
	RequestID string `json:"request_id"`
	Endpoint  string `json:"endpoint"`
}

type Response struct {
	RequestID string          `json:"request_id"`
	Data      json.RawMessage `json:"data"`
}

func handle(msg pulsar.Message, consumer pulsar.Consumer) {
	task := Task{}
	err := json.Unmarshal(msg.Payload(), &task)
	if err != nil {
		log.Fatalf("Could not unmarshal message: %v", err)
		consumer.Ack(msg)
		return
	}

	endpoint := task.Endpoint

	data, err := json.Marshal(Response{
		RequestID: task.RequestID,
		Data:      json.RawMessage(STATIC_RESPONSE),
	})

	if err != nil {
		log.Printf("Could not marshal response: %v", err)
		consumer.Ack(msg)
		return
	}

	res, err := http.Post(endpoint, "application/json", strings.NewReader(string(data)))

	defer res.Body.Close()

	if err != nil {
		log.Printf("Could not send response: %v", err)
		consumer.Ack(msg)
		return
	}

	if res.StatusCode != http.StatusOK {
		log.Printf("Could not send response: %v, %s", res.Status, endpoint)
		consumer.Ack(msg)
		return
	}

	consumer.Ack(msg)
}

func main() {
	// 创建 Pulsar 客户端
	client, err := pulsar.NewClient(pulsar.ClientOptions{
		URL: PULSAR_URL,
	})
	if err != nil {
		log.Fatalf("Could not create Pulsar client: %v", err)
	}
	defer client.Close()

	consumer, err := client.Subscribe(pulsar.ConsumerOptions{
		Topic:            "model-" + MODEL_NAME,
		SubscriptionName: "model-" + MODEL_NAME + "-subscription",
		Type:             pulsar.Shared,
	})
	if err != nil {
		log.Fatalf("Could not subscribe to topic: %v", err)
	}
	defer consumer.Close()

	log.Printf("Subscribed successfully")
	for {
		msg, err := consumer.Receive(context.Background())
		if err != nil {
			log.Fatalf("Could not receive message: %v", err)
		}

		go handle(msg, consumer)
	}
}
