#!/bin/bash
source .venv/bin/activate

APP_NAME="Phase2"
ENV_NAME="phase2-env"
REGION="us-east-1"
PLATFORM="python-3.11"

echo "Initializing Elastic Beanstalk app..."
eb init -p $PLATFORM $APP_NAME --region $REGION

if eb status $ENV_NAME >/dev/null 2>&1; then
    echo "Terminating old environment: $ENV_NAME"
    eb terminate $ENV_NAME --force
    echo "Waiting 30s for termination..."
    sleep 30
fi

echo "Creating new environment: $ENV_NAME"
eb create $ENV_NAME --platform $PLATFORM

echo "Deploying application..."
eb deploy $ENV_NAME

echo "Opening the app..."
eb open $ENV_NAME

eb health $ENV_NAME
