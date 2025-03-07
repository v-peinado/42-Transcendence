#!/bin/bash
# this script is used to load the IP_SERVER variable from the .env file

# Check if .env file exists
if [ ! -f ./.env ]; then
    echo "Error: .env file not found in the current directory"
    exit 1
fi

# Load the IP_SERVER variable from the .env file
source .env

# Check if IP_SERVER was defined in .env
if [ -z "$IP_SERVER" ]; then
    echo "Error: IP_SERVER variable not defined in .env file"
    exit 1
fi

# Export the IP_SERVER variable
export IP_SERVER

# Mostrar mensaje informativo
echo "Exported IP: IP_SERVER=$IP_SERVER"
