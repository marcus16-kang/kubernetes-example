# Kubernetes Dashboard with AWS ALB (Feat. Subdomain)

## Deploy CloudFront Distribution

### Download `cloudfront-template.yaml`

You can download template from [HERE](./cloudfront-template.yaml).

### Deploy CloudFormation Stack

``` shell
STACK_NAME=<stack name>
REGION=<region code>
ALB_DNS_NAME = $(kubectl get ing alb-ingress-kubernetes-dashboard -n ingress-nginx --output jsonpath={.status.loadBalancer.ingress[].hostname})

(aws cloudformation create-stack \
    --template-body file://cloudfront-template.yaml \
    --parameters ParameterKey=DashboardALBDNSName,ParameterValue=$ALB_DNS_NAME \
    --stack-name $STACK_NAME \
    --region $REGION > /dev/null & \
) && watch "aws cloudformation describe-stack-events \
    --stack-name $STACK_NAME \
    --region $REGION | \
        jq -r '.StackEvents[] |
            \"\\(.Timestamp | sub(\"\\\\.[0-9]+Z$\"; \"Z\") | fromdate | strftime(\"%H:%M:%S\") ) \\(.LogicalResourceId) \\(.ResourceType) \\(.ResourceStatus)\"
        ' | column -t"
```

***Why we deploy CloudFront Distribution?***

Kubernetes Dashboard allows only HTTPS connection. You cannot access dashboard through HTTP.