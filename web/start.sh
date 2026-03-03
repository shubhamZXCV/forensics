#!/bin/bash

# activating venv
source ../venv_django/bin/activate

# Default version is v1
export APP_VERSION="v1"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --version|-v) export APP_VERSION="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "--- Starting Application in $APP_VERSION Mode ---"

# Redis is not available, using filesystem broker.

# Start Celery in background
echo "Starting Celery..."
rm -f celery.log
celery -A forensic_pipeline worker -l info --logfile=celery.log --detach

# Stream Celery logs to console in background
tail -f celery.log &
TAIL_PID=$!

# Function to kill tail on exit
cleanup() {
    echo "Stopping log stream..."
    kill $TAIL_PID
}
trap cleanup EXIT

# Start Django Server
echo "Starting Django Server..."
python3 manage.py runserver 0.0.0.0:8000
