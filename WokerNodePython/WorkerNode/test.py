import pulsar

client = pulsar.Client('pulsar://localhost:6650')

producer = client.create_producer('my-topic')

for i in range(10):
    producer.send(('Hello-%d' % i).encode('utf-8'))

consumer = client.subscribe('my-topic','my-subscription')

while True :
    msg = consumer.receive()
    try:
        print("received message: '{}' id = '{}'".format(msg.data(),msg.message_id()))
        consumer.acknowledge(msg)
    except Exception:
        consumer.negative_acknowledge(msg)

client.close()