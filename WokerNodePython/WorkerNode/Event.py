from kubernetes import client,config
import os
import time

def createEvent(apiInstance,namespace,podName,reason,message):
    event = client.CoreV1Event(
        metadata=client.V1ObjectMeta(
            name=f'{podName}.webpage-error',
            namespace=namespace,
        ),
        involved_object=client.V1ObjectReference(
            kind='Pod',
            name=podName,
            namespace=namespace,
        ),
        reason=reason,
        message=message,
        type='Warning',
        source=client.V1EventSource(
            component='webpage-app',
        ),
        first_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        last_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )

    apiInstance.create_namespace_event(namespace,event)