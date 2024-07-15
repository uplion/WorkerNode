#!/usr/bin/env bash

curl -X POST -d '{"model": "static","messages": [{"role": "user","content": "Hello"}]}' http://localhost:8081/api/v1/chat/completions -v

