import requests
from requests.auth import HTTPBasicAuth
import os
import sys
import json

# Load ONOS credentials from environment variables
onos_url = os.getenv('ONOS_URL', 'http://localhost:8181')
onos_username = os.getenv('ONOS_USERNAME', 'onos')
onos_password = os.getenv('ONOS_PASSWORD', 'rocks')

PRIORITY = 40000
APP_ID = 'org.onosproject.rest'

# Stores the path to be installed in ONOS
ROUTING_PATH1 = [
    {
        "deviceId": "of:0000000000000001",
        "inputPort": "3",
        "outputPort": "2",
    },
    {
        "deviceId": "of:0000000000000003",
        "inputPort": "2",
        "outputPort": "3",
    },
    {
        "deviceId": "of:0000000000000004",
        "inputPort": "3",
        "outputPort": "1",
    },
    {
        "deviceId": "of:0000000000000005",
        "inputPort": "1",
        "outputPort": "3",
    },
    {
        "deviceId": "of:0000000000000009",
        "inputPort": "3",
        "outputPort": "1",
    },
    {
        "deviceId": "of:0000000000000008",
        "inputPort": "2",
        "outputPort": "3",
    },
]

ROUTING_PATH2 = [
    {
        "deviceId": "of:0000000000000001",
        "inputPort": "3",
        "outputPort": "1",
    },
    {
        "deviceId": "of:0000000000000002",
        "inputPort": "1",
        "outputPort": "2",
    },
     {
        "deviceId": "of:0000000000000003",
        "inputPort": "1",
        "outputPort": "3",
    },
    {
        "deviceId": "of:0000000000000004",
        "inputPort": "3",
        "outputPort": "2",
    },
        {
        "deviceId": "of:0000000000000006",
        "inputPort": "2",
        "outputPort": "1",
    },
    {
        "deviceId": "of:0000000000000005",
        "inputPort": "2",
        "outputPort": "3",
    },
    {
        "deviceId": "of:0000000000000009",
        "inputPort": "3",
        "outputPort": "2",
    },
    {
        "deviceId": "of:0000000000000007",
        "inputPort": "2",
        "outputPort": "1",
    },
    {
        "deviceId": "of:0000000000000008",
        "inputPort": "1",
        "outputPort": "3",
    },
]

def install_flow_in_device(device_id, app_id, flow_rule):
    url = f"{onos_url}/onos/v1/flows/{device_id}"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=flow_rule, headers=headers, auth=HTTPBasicAuth(onos_username, onos_password))

    if response.status_code == 201:
        print(f"Flow rule installed successfully on {device_id}\n")
    else:
        print(f"Failed to install flow rule on {device_id}: {response.text}\n")

def create_flow(device_id, input_port, output_port):
    # Define the flow rule
    flow_rule = {
        "priority": PRIORITY,
        "timeout": 0,
        "isPermanent": True,
        "deviceId": device_id,
        "treatment": {
            "instructions": [
                {
                    "type": "OUTPUT",
                    "port": output_port
                }
            ]
        },
        "selector": {
            "criteria": [
                {
                    "type": "IN_PORT",
                    "port": input_port
                }
            ]
        }
    }
    return flow_rule

def delete_old_flows():
    print("Deleting old flows")
    url = f"{onos_url}/onos/v1/flows/application/{APP_ID}"
    print(f"Using URL: {url}")
    headers = {'Accept': 'application/json'}
    response = requests.delete(url, headers=headers, auth=HTTPBasicAuth(onos_username, onos_password))
    
    if response.status_code == 204:
        print("Old flow rules deleted successfully.\n")
    else:
        print(f"Failed to delete old flow rules: {response.status_code}: {response.text}\n")
    

def install_path(path):
    delete_old_flows()
    for device in path:
        device_id = device["deviceId"]
        input_port = device["inputPort"]
        output_port = device["outputPort"]

        flow1 = create_flow(device_id, input_port, output_port)
        flow2 = create_flow(device_id, output_port, input_port)

        # Install the flow rule in the device
        install_flow_in_device(device_id, APP_ID, flow1)
        install_flow_in_device(device_id, APP_ID, flow2)


if __name__ == "__main__":  
    # Check command line arguments 
    if len(sys.argv) == 2:
        path_id = sys.argv[1]
        if path_id == "0":
            delete_old_flows()
        elif path_id == "1":
            path = ROUTING_PATH1
            install_path(path)
        elif path_id == "2":
            path = ROUTING_PATH2
            install_path(path)
        else:
            print("Invalid path ID. Please provide a valid path ID.")
            sys.exit(1)
        
