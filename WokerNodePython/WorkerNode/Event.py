from kubernetes import client,config
import os
import time

def createEvent(apiInstance,AIModelNamespace,AIModelName,reason,message):
    if(AIModelName == 'none'):
        print(
            'An error occured!\nreason: {}\nmessage: {}'.format(reason,message)
        )
    else:
        event = client.CoreV1Event(
        metadata=client.V1ObjectMeta(
            name=f'{AIModelName}.workerNode-error',
            namespace=AIModelNamespace,
        ),
        involved_object=client.V1ObjectReference(
            kind='AIModel',
            name=AIModelName,
            namespace=AIModelNamespace,
        ),
        reason=reason,
        message=message,
        type='Warning',
        source=client.V1EventSource(
            component='WorkerNode',
        ),
        first_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        last_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
        apiInstance.create_namespace_event(AIModelNamespace,event)
    