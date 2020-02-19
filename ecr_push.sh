#!/usr/bin/env bash

aws ecr get-login-password --region=us-east-2 | docker login --username AWS --password-stdin https://617608773253.dkr.ecr.us-east-2.amazonaws.com
docker build -t tots . -f ./docker/production/Dockerfile
docker tag tots:latest 617608773253.dkr.ecr.us-east-2.amazonaws.com/tots:latest
docker push 617608773253.dkr.ecr.us-east-2.amazonaws.com/tots:latest
