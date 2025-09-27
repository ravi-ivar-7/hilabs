#!/bin/bash

echo "Waiting for MinIO to be ready..."
sleep 10
mc alias set hilabs http://localhost:9000 ${MINIO_ROOT_USER:-hilabs} ${MINIO_ROOT_PASSWORD:-hilabs123456}

echo "Creating MinIO buckets..."
mc mb hilabs/contracts-tn --ignore-existing
mc mb hilabs/contracts-wa --ignore-existing
mc mb hilabs/templates --ignore-existing
mc mb hilabs/processed --ignore-existing

mc anonymous set download hilabs/processed
mc anonymous set none hilabs/contracts-tn
mc anonymous set none hilabs/contracts-wa
mc anonymous set none hilabs/templates

mc ls hilabs/
