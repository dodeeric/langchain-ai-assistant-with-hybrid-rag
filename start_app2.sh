#!/bin/bash

# Define the application name
SERVICE_NAME="assistant"

# Define the user that should be running the service
SERVICE_USER="codespace"

# Define the keyword to identify the process
KEYWORD="streamlit"

# Define the folder where the application is located
FOLDER="./"

# Function to start the service
start_service() {
    if [[ `/usr/bin/whoami` == $SERVICE_USER ]]; then
        pushd .
        echo "Starting $SERVICE_NAME..."
        cd $FOLDER
        # Command to start the Streamlit application
        streamlit run assistant_v11.py --server.port=8080 &
        sleep 20
        PROC=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
        if [ -n "$PROC" ] && [ "$PROC" != "" ]; then
            echo "OK: system started."
        else
            echo "ERROR: system process not found!"
        fi
        echo "script execution finished!"
        popd
    else
        echo "User must be $SERVICE_USER !"
    fi
}

# Function to stop the service
stop_service() {
    if [[ `/usr/bin/whoami` == $SERVICE_USER ]]; then
        pushd .
        echo "Stopping $SERVICE_NAME......"
        # Get the process ID
        processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
        echo "Trying to kill process with key $SERVICE_NAME - ignore error messages below."
        kill $processPID
        sleep 10
        while [ -n "$processPID" ]; do
            echo "Waiting process ($processPID) to shutdown..."
            sleep 10
            processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
        done
        echo "Ensured process with key $SERVICE_NAME is no longer running."
        popd
    else
        echo "User must be $SERVICE_USER !"
    fi
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
