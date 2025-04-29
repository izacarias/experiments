#!/usr/bin/env python3

import os
import requests
import time
import threading
from requests.auth import HTTPBasicAuth
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import Intf, TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.util import customClass
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, WriteOptions, Point

# Load environment variables from .env file
load_dotenv()

# sflow-r configuration
sflowrt_url = os.getenv('SFLOWRT_URL', 'http://localhost:8008')
influxdb_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
influxdb_token = os.getenv('INFLUXDB_TOKEN')
influxdb_org = os.getenv('INFLUXDB_ORG')
influxdb_bucket = os.getenv('INFLUXDB_BUCKET')
# ONOS
onos_url = os.getenv('ONOS_URL', 'http://localhost:8181'    )
onos_username = os.getenv('ONOS_USERNAME', 'onos')
onos_password = os.getenv('ONOS_PASSWORD', 'rocks')

# Add historical data storage
onos_link_history = {}  # Format: {(device_id, port_id): {'bytes': value, 'duration': value}}

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

# Enables sflow monitoring on OVS Switches
exec(open('sflow.py').read())

# Initialize InfluxDB client
influxdb_client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
influxdb_write_api = influxdb_client.write_api(write_options=WriteOptions(batch_size=1))


# Get links from ONOS
def onos_get_links():
    url = '%s/onos/v1/links' % onos_url
    response = requests.get(url, auth=HTTPBasicAuth(onos_username, onos_password))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get links from ONOS: {response.status_code} {response.text}")


# Get link usage from ONOS
def onos_get_port_stats(device_id, port_id):
    url = "%s/onos/v1/statistics/ports/%s/%s" % (onos_url, device_id, port_id)
    response = requests.get(url, auth=HTTPBasicAuth(onos_username, onos_password))
    response.raise_for_status()
    return response.json()


def onos_get_link_usage():
    global onos_link_history
    return_value = []
    links = onos_get_links()
    for link in links['links']:
        src_device = link['src']['device']
        src_port = link['src']['port']
        dst_device = link['dst']['device']
        
        # Get statistics for the source device
        src_stats = onos_get_port_stats(src_device, src_port)
        current_bytes = src_stats.get('statistics')[0].get('ports')[0].get('bytesSent')
        current_duration = src_stats.get('statistics')[0].get('ports')[0].get('durationSec')
        
        # Get historical data
        link_key = (src_device, src_port)
        prev_stats = onos_link_history.get(link_key, {'bytes': current_bytes, 'duration': current_duration})
        
        # Calculate delta values
        bytes_delta = current_bytes - prev_stats['bytes']
        duration_delta = current_duration - prev_stats['duration']
        
        # Calculate data rate
        datarate = (bytes_delta * 8) / duration_delta if duration_delta > 0 else 0
        
        # Update historical data
        onos_link_history[link_key] = {
            'bytes': current_bytes,
            'duration': current_duration
        }
        debug("Datarate for %s to %s: %d bps \n" % (src_device, dst_device, datarate))
        return_value.append((src_device, dst_device, datarate))
    return return_value


# Define sflow-rt flow if not exists
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


# Get flow value
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


def export_to_influxdb(stop_event):
    while not stop_event.is_set():
        try:
            # get flow names
            flow_keys = sflow_flows.keys()
            monitored_hosts = [['10.0.0.1', '10.0.0.2']]
            influx_timestamp = time.time_ns()
            flow_collected = False
            for host_pair in monitored_hosts:
                src_host = host_pair[0]
                dst_host = host_pair[1]
                # boolean to indicate wheter data was collected
                for flow in flow_keys:
                    flow_value = get_flow_value(flow, src_host, dst_host)
                    if flow_value is not None:
                        flow_collected = flow_collected or True
                        point = Point(flow) \
                            .tag("flow_type", flow) \
                            .tag("ip_src", src_host) \
                            .tag("ip_dst", dst_host) \
                            .field("value", float(flow_value)) \
                            .time(influx_timestamp)
                        influxdb_write_api.write(influxdb_bucket, influxdb_org, point)
                        debug("InfluxDB point written successfully\n")
            if flow_collected:
                return_value = onos_get_link_usage()
                for src_device, dst_device, datarate in return_value:
                    point = Point("link_usage") \
                        .tag("src_device", src_device) \
                        .tag("dst_device", dst_device) \
                        .field("datarate", float(datarate)) \
                        .time(influx_timestamp)
                    influxdb_write_api.write(influxdb_bucket, influxdb_org, point)
            time.sleep(1)
        except Exception as e:
            info("Error exporting to InfluxDB: %s \n" % e)
            time.sleep(1)


def remove_hsflow_pids(host_nodes):
    for host in host_nodes:
        info( '*** Removing old hsflowd pid files for host %s \n' % host.name)
        os.system( 'rm ./hsflow/%s.pid' % host.name)


def delete_veth_pairs(host_names):
    for host in host_names:
        os.system( 'ip link del root-%s' % host )


def create_veth_pairs(host_names):
    # get machine IP address
    local_ip = os.popen('hostname -I').read().split()[0]
    vm_ip = local_ip + '/24'
    # get the network address from the IP
    network = local_ip.split('.')

    mininet_host_ip = 100
    for host in host_names:
        # create IP addresses for machines
        mininet_host_ip += 1
        internal_ip = network[0] + '.' + network[1] + '.' + network[2] + '.' + str(mininet_host_ip) + '/32'
        info("*** Creating veth pair for %s\n" % host)
        os.system( 'ip link add root-%s type veth peer name %s-root' % (host, host) )
        os.system( 'ip link set root-%s up' % host )
        os.system( 'ip addr add %s dev root-%s' % (vm_ip, host) )
        os.system( 'ip route add %s dev root-%s' % (internal_ip, host) )


def add_external_interfaces(host_names, net):
    for host in host_names:
        info("*** Adding interface to root namespace for host %s\n" % host)
        iface_name = host + '-root'
        _intf = Intf( iface_name, net.get(host))


def configure_host_ip(net):
    local_ip = os.popen('hostname -I').read().split()[0]
    host_network = local_ip.split('.')
    vm_ip_base = host_network[0] + '.' + host_network[1] + '.' + host_network[2]
    host_network = host_network[0] + '.' + host_network[1] + '.' + host_network[2] + '.0/24'
    mininet_host_ip = 100
    # get the network address from the IP
    host_nodes = net.hosts
    for host in host_nodes:
        mininet_host_ip += 1
        host_intf = host.name + '-root'
        internal_ip = vm_ip_base + '.' + str(mininet_host_ip) + '/24'
        host.cmd( ' ip addr add %s dev %s' % (internal_ip, host_intf) )
        host.cmd( ' ip route add %s dev %s' % (host_network, host_intf) )


class CustomTopology(Topo):
    def build(self):
        # Create switches for group g1
        g1_sw1 = self.addSwitch('s1', protocols="OpenFlow13")
        g1_sw2 = self.addSwitch('s2', protocols="OpenFlow13")
        g1_sw3 = self.addSwitch('s3', protocols="OpenFlow13")

        # Create switches for group g2
        g2_sw4 = self.addSwitch('s4', protocols="OpenFlow13")
        g2_sw5 = self.addSwitch('s5', protocols="OpenFlow13")
        g2_sw6 = self.addSwitch('s6', protocols="OpenFlow13")

        # Create switches for group g3
        g3_sw7 = self.addSwitch('s7', protocols="OpenFlow13")
        g3_sw8 = self.addSwitch('s8', protocols="OpenFlow13")
        g3_sw9 = self.addSwitch('s9', protocols="OpenFlow13")

        # Connect switches within group g1
        self.addLink(g1_sw1, g1_sw2, bw=99)    # l_1
        self.addLink(g1_sw2, g1_sw3, bw=96)    # l_2
        self.addLink(g1_sw1, g1_sw3, bw=100)    # l_3
        
        # Connect switches within group g2
        self.addLink(g2_sw4, g2_sw5, bw=93)    # l_4
        self.addLink(g2_sw5, g2_sw6, bw=100)    # l_5
        self.addLink(g2_sw4, g2_sw6, bw=95)    # l_6
        
        # Connect switches within group g3
        self.addLink(g3_sw7, g3_sw8, bw=89)    # l_7
        self.addLink(g3_sw8, g3_sw9, bw=91)    # l_8
        self.addLink(g3_sw7, g3_sw9, bw=97)    # l_9

        # Connect each group via links
        # g1 to g2
        self.addLink(g1_sw3, g2_sw4, bw=97)    # l_10
        # g2 to g3
        self.addLink(g2_sw5, g3_sw9, bw=86)    # l_11

        # Add hosts and connect to specific switches
        host1 = self.addHost('h1')  # Host in group g1
        host2 = self.addHost('h2')  # Host in group g3

        # Connect hosts to the switches
        self.addLink(host1, g1_sw1)     # l_12
        self.addLink(host2, g3_sw8)     # l_13


def runNetwork():
    setLogLevel('info')      # Set the logging level
    topo = CustomTopology()  # Create the topology
    net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink, build=False)  # Set up the network

    # Adding External controller
    c0 = net.addController(name='c0', controller=RemoteController, ip='localhost', protocol='tcp',port=6653)

    # Build the network (to get access to hosts)
    net.build()
    # Get all host nodes    # Get all host nodes
    host_nodes = net.hosts
    host_names = [host.name for host in host_nodes]
    info("*** Host names: %s\n" % host_names)
    # Create veth pairs for hosts
    info( '*** Deleting old virtual ethernet pairs\n' )
    delete_veth_pairs(host_names)
    info( '*** Creating the virtual ethernet pairs to communicate with the host\n' )
    create_veth_pairs(host_names)

    # Add network interfaces to the root namespace into Mininet hosts
    info( '*** Adding interface to root namespace\n')
    add_external_interfaces(host_names, net)

    net.start()
    info("*** Network is running. \n")

    # Configure IP addresses for hosts to communicate with the root namespace
    configure_host_ip(net)

    remove_hsflow_pids(host_nodes)
    
    for host in host_nodes:
        info( '*** Running hsflow process in %s \n' % host.name)
        host.cmd( '/usr/sbin/hsflowd -dd -f ./hsflow/%s.conf -p ./hsflow/%s.pid -D ./hsflow/%s.log &' % (host.name, host.name, host.name))

    #stop event for the thread
    stop_event = threading.Event()
    export_thread = threading.Thread(target=export_to_influxdb, args=(stop_event,))
    export_thread.daemon = True
    export_thread.start()

    info("*** Start Iperf server on host h2\n")
    h2 = net.get('h2')
    h2.cmd('iperf -s &')
    # start another iperf server on h2 for udp backrgound traffic
    h2.cmd('iperf -s -u -p 5002 &')

    info("*** Start Iperf client on host h1 (TCP)\n")
    h1 = net.get('h1')
    h1.cmd('iperf -c 10.0.0.2 -t 600 &')
    info("*** Start Iperf client on host h1 (UDP)\n")
    # start another iperf client on h1 for udp background traffic
    h1.cmd('iperf -c 10.0.0.2 -b 10M -t 600 -u -p 5002 &')
    

    time.sleep(600)
    info("*** Running Mininet CLI\n")
    CLI(net)  # Start the mininet command line interface
    
    # Stop thread
    stop_event.set()
    export_thread.join(timeout=3)




    net.stop()  # Stop the network when done


    info( '*** Deleting old virtual ethernet pairs\n' )
    delete_veth_pairs(host_names)

    # remove hsflow pid from folder ./hsflow
    remove_hsflow_pids(host_nodes)
    

if __name__ == '__main__':
    define_sflowrt_flow()
    runNetwork()
