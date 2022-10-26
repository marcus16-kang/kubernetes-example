import os
import json
import boto3
import yaml
import tempfile
import base64
import eks_token
from botocore.config import Config
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_role():
    lambda_client = boto3.client('lambda')
    role_response = lambda_client.get_function_configuration(
        FunctionName=os.getenv('AWS_LAMBDA_FUNCTION_NAME')
    )

    print(role_response['Role'])

    return role_response['Role']

def create_hpa_status_object(desired_replicas):
    status = client.V2HorizontalPodAutoscalerStatus(
        desired_replicas=desired_replicas
    )

    return status

def write_cafile(data):
    cafile = tempfile.NamedTemporaryFile(delete=False)
    cadata_b64 = data
    cadata = base64.b64decode(cadata_b64)
    cafile.write(cadata)
    cafile.flush()

    return cafile

def get_token(cluster_name):
    return eks_token.get_token(cluster_name)['status']['token']

def k8s_api_client(endpoint, token, cafile):
    kconfig = config.kube_config.Configuration(
        host=endpoint,
        api_key={'authorization': 'Bearer ' + token}
    )
    kconfig.ssl_ca_cert = cafile
    
    return client.ApiClient(configuration=kconfig)

def lambda_handler(event, context):
    # get variables
    REGION = os.getenv('REGION')
    CLUSTER_NAME = os.getenv('CLUSTER_NAME')
    ROLE_ARN = get_role()
    NAMESPACE_NAME = os.getenv('HPA_NAMESPACE_NAME')
    DEPLOYMENT_NAME = os.getenv('HPA_DEPLOYMENT_NAME')

    # confib boto3
    boto3_config = Config(
        region_name = REGION,
    )

    # get kubernetes authentication information
    eks_client = boto3.client('eks', config=boto3_config)
    response = eks_client.describe_cluster(name=CLUSTER_NAME)
    endpoint = response['cluster']['endpoint']
    certificate = response['cluster']['certificateAuthority']['data']
    cafile = write_cafile(certificate)
    
    api_client = k8s_api_client(
        endpoint=endpoint,
        token=get_token(CLUSTER_NAME),
        cafile=cafile.name
    )

    # get hpa status
    with api_client:
        api_instance_read_hpa_status = client.AutoscalingV2Api(api_client=api_client)
    ret = api_instance_read_hpa_status.read_namespaced_horizontal_pod_autoscaler_status(
        name=DEPLOYMENT_NAME,
        namespace=NAMESPACE_NAME
    )

    max_replicas = ret.spec.max_replicas
    current_replicas = ret.status.current_replicas
    print('max : {} | current : {}'.format(max_replicas, current_replicas))

    # set desired replicas
    if current_replicas < max_replicas:  # up
        desired_replicas = current_replicas + 1
    else:
        desired_replicas = current_replicas
    
    # read deployment spec
    try:
        with api_client:
            api_instance_deployment = client.AppsV1Api(api_client=api_client)
        
        ret_deployment = api_instance_deployment.read_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE_NAME
        )
        ret_deployment.spec.replicas = desired_replicas
    
    except ApiException as e:
        print("Exception when calling AppsV1Api->read_namespaced_deployment: %s\n" % e)
    
    # update deployment spec
    try:
        with api_client:
            api_instance_deployment = client.AppsV1Api(api_client=api_client)
        
        ret = api_instance_deployment.patch_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE_NAME,
            body=ret_deployment
        )
    
    except ApiException as e:
        print("Exception when calling AppsV1Api->patch_namespaced_deployment: %s\n" % e)

    return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Hello, World!'
                })
            }