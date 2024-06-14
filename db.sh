#!/bin/bash

# Ragai - (c) Eric Dodémont, 2024.

# Define the application name
SERVICE_NAME="chroma"

# Define the keyword to identify the process
KEYWORD="python3"

# Define the folder where the application is located
FOLDER="./"

# Function to start the service
start_service() {
    pushd . > /dev/null
    echo "Starting $SERVICE_NAME..."
    cd $FOLDER
    # Command to start the Streamlit application
    nohup chroma run --host 0.0.0.0 --port 8000 --path ./chromadb &
    sleep 5
    PROC=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
    if [ -n "$PROC" ] && [ "$PROC" != "" ]; then
        echo "OK: system started."
    else
        echo "ERROR: system process not found!"
    fi
    popd > /dev/null
}

# Function to stop the service
stop_service() {
    pushd . > /dev/null
    echo "Stopping $SERVICE_NAME..."
    # Get the process ID
    processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
    echo "Trying to kill process with key $SERVICE_NAME."
    kill $processPID
    sleep 5
    while [ -n "$processPID" ]; do
        echo "Waiting process ($processPID) to shutdown..."
        sleep 5
        processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
    done
    echo "OK: system stopped."
    popd > /dev/null
}

# Function to restart the service
restart_service() {
    stop_service
    start_service
}

# Main program
if [ "$1" == "start" ]; then
    start_service
elif [ "$1" == "stop" ]; then
    stop_service
elif [ "$1" == "restart" ]; then
    restart_service
else
    echo "Invalid command. Please use 'start', 'stop', or 'restart'."
fi
