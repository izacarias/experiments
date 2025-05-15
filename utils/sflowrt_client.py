import requests
import os
from mininet.log import debug, info

# Definition of sflow-rt- flows
sflow_flows = {
    "tcprtt": {
        "keys": "ipsource,ipdestination,tcpsourceport,tcpdestinationport",
        "value": "tcprtt"
    },
    "tcpcwndsnd": {
        "keys": "ipsource,ipdestination,tcpsourceport,tcpdestinationport",
        "value": "tcpcwndsnd"
    },
    "tcpwindow": {
        "keys": "ipsource,ipdestination,tcpsourceport,tcpdestinationport",
        "value": "tcpwindow"
    },
    "tcplost": {
        "keys": "ipsource,ipdestination,tcpsourceport,tcpdestinationport",
        "value": "tcplost"
    },
    "tcpretrans": {
        "keys": "ipsource,ipdestination,tcpsourceport,tcpdestinationport",
        "value": "tcpretrans"
    },
    "tcpunacked": {
        "keys": "ipsource,ipdestination,tcpsourceport,tcpdestinationport",
        "value": "tcpunacked"
    }
}

sflowrt_url = os.getenv('SFLOWRT_URL', 'http://localhost:8008')

####################################
# Define sflow-rt flow if not exists
####################################
def define_sflowrt_flow():
    for flow, flow_definition in sflow_flows.items():
        flow_url = '%s/flow/%s/json' % (sflowrt_url, flow)
        debug("Quering for sflow flow definition "+ flow)
        response = requests.get(flow_url)
        if response.status_code == 404:
            response = requests.put(flow_url, json=flow_definition)
            if response.status_code in [200, 204]:
                print("sflow-rt flow defined successfully")
            else:
                raise Exception(f"Failed to define sflow-rt flow: {response.status_code} {response.text}")
                
        else:
            print("sflow-rt: flow " + flow + " already exists")

####################################
# Get flow value
####################################
def get_flow_value(flow, src_host, dst_host):
    flow_url = '%s/activeflows/ALL/%s/json' % (sflowrt_url, flow)
    response = requests.get(flow_url)
    if response.status_code == 200:
        for flow_item in response.json():
            key = flow_item.get('key')
            key_parts = key.split(',')
            if key_parts[0] == src_host and key_parts[1] == dst_host:
                flow_value = flow_item.get('value')
                debug("sflow-rt value for flow %s(src: %s dst: %s): %s\n" % (flow, src_host, dst_host, flow_value))
                return flow_value
        
    else:
        info("Failed to get flow %s value: %s %s" % (flow, response.status_code, response.text))
        return None

