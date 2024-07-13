FROM python:3.8-slim

COPY WorkerNode.py Event.py ApiMessageProcessor.py requirement.txt /
RUN pip install -r requirement.txt
ENV API_URL="https://api.openai-hk.com/v1/chat/completions" API_KEY="hk-tt0bid1000037138c7e471957c0a93b0017f480b002f24ae" PULSAR_URL="pulsar://172.25.32.1:6650"

