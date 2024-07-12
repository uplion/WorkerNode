#!/bin/bash
stream=false
if [ "$1" == "stream" ]; then
  stream=true
fi

data=$(jo -p model="gpt-3.5-turbo" messages=$(jo -a $(jo role="user" content="Write a 300 words story")) stream=$stream)

curl -X POST -H "Content-Type: application/json" -d "$data" http://localhost:8081/api/v1/chat/completions -v
