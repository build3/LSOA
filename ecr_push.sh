#!/usr/bin/env bash

$(aws ecr get-login-password --no-include-email --region us-east-2)
docker build -t tots . -f ./docker/production/Dockerfile
docker tag tots:latest 617608773253.dkr.ecr.us-east-2.amazonaws.com/tots:latest
docker push 617608773253.dkr.ecr.us-east-2.amazonaws.com/tots:latest
