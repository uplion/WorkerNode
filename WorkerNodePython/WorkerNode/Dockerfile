FROM python:3.8-slim

COPY WorkerNode.py Event.py ApiMessageProcessor.py requirement.txt local.sh ai.sh start.sh /
RUN pip install -r requirement.txt

CMD ["python3","WorkerNode.py"]