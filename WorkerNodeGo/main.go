package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/apache/pulsar-client-go/pulsar"
)

const MODEL_NAME = "static"

var PULSAR_URL string
var MAX_PROCESS_NUM int
var LIMIT bool = false
var PROCESSING int = 0
var LOCK sync.Mutex
var LOCK_CHAN = make(chan int, 1)

func init() {
	if v, ok := os.LookupEnv("PULSAR_URL"); ok {
		PULSAR_URL = v
	} else {
		PULSAR_URL = "pulsar://localhost:6650"
	}

	if v, ok := os.LookupEnv("MAX_PROCESS_NUM"); ok {
		var err error
		MAX_PROCESS_NUM, err = strconv.Atoi(v)
		if err != nil {
			log.Fatalf("Could not parse MAX_PROCESS_NUM: %v", err)
		}

		if MAX_PROCESS_NUM <= 10 {
			LIMIT = true
		}
	} else {
		MAX_PROCESS_NUM = 0
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
	defer func() {
		if LIMIT {
			LOCK.Lock()
			PROCESSING--
			LOCK.Unlock()
			select {
			case LOCK_CHAN <- 1:
			default:
			}
		}
	}()
	task := Task{}
	if LIMIT {
		log.Printf("Recv message: %s", string(msg.Payload()))
	}
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

	if LIMIT {
		time.Sleep(1 * time.Second)
	}

	res, err := http.Post(endpoint, "application/json", strings.NewReader(string(data)))

	if err != nil {
		log.Printf("Could not send response: %v", err)
		consumer.Ack(msg)
		return
	}

	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		log.Printf("Could not send response: %v, %s", res.Status, endpoint)
		consumer.Ack(msg)
		return
	}

	consumer.Ack(msg)
}

func main() {
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
		if LIMIT {
			for {
				LOCK.Lock()
				if PROCESSING < MAX_PROCESS_NUM {
					LOCK.Unlock()
					break
				}
				LOCK.Unlock()
				log.Printf("Processing limit reached, waiting for free slot")
				<-LOCK_CHAN
			}
		}
		msg, err := consumer.Receive(context.Background())
		if err != nil {
			log.Fatalf("Could not receive message: %v", err)
		}

		if LIMIT {
			LOCK.Lock()
			PROCESSING++
			LOCK.Unlock()
		}
		go handle(msg, consumer)
	}
}
