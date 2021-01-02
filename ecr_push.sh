#!/usr/bin/env bash
AWS_REGION=us-east-1
aws ecr get-login-password --region=${AWS_REGION} | docker login --username AWS --password-stdin https://617608773253.dkr.ecr.${AWS_REGION}.amazonaws.com
docker build -t tots . -f ./docker/production/Dockerfile
docker tag tots:latest 617608773253.dkr.ecr.${AWS_REGION}.amazonaws.com/tots:latest
docker push 617608773253.dkr.ecr.${AWS_REGION}.amazonaws.com/tots:latest
