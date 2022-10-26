#!/bin/bash

eksctl create iamserviceaccount \
	--name nginx-sa \
	--namespace default \
	--cluster <CLUSTER NAME> \
	--role-name "<ROLE NAME>" \
	--attach-policy-arn arn:aws:iam::aws:policy/AmazonKinesisFullAccess \
	--approve
