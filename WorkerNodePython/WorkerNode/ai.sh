#!/bin/bash
stream=false
if [ "$1" == "stream" ]; then
  stream=true
fi

data=$(jo -p model="TinyLlama-1.1B" messages=$(jo -a $(jo role="user" content="Hello!")) stream=$stream)

curl -X POST -H "Content-Type: application/json" -d "$data" http://localhost:8081/api/v1/chat/completions -v
