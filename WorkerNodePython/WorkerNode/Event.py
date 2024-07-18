from kubernetes import client,config
import os
import time

AIModelNamespace = os.getenv('AIMODEL_NAMESPACE')
AIModelName = os.getenv('AIMODEL_NAME')
apiInstance = None


def kubenetesInit():
    try:
        config.load_incluster_config()
    except:
        try:
            config.load_kube_config()
        except Exception as e:
            print(e)
            return
    global apiInstance
    apiInstance = client.CoreV1Api()

if AIModelName:
    kubenetesInit()

def createEvent(reason,message):
    print(
        'An error occured!\nreason: {}\nmessage: {}'.format(reason,message)
    )
    if AIModelName:
        event = client.CoreV1Event(
        metadata=client.V1ObjectMeta(
            generate_name=f'{AIModelName}.workerNode-error-',
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
        apiInstance.create_namespaced_event(AIModelNamespace,event)
    