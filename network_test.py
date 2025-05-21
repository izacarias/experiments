#!/usr/bin/env python3

import os
import requests
import time
import threading
from datetime import datetime
from requests.auth import HTTPBasicAuth
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import Intf, TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.util import customClass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# sflow-r configuration
influxdb_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
influxdb_token = os.getenv('INFLUXDB_TOKEN')
influxdb_org = os.getenv('INFLUXDB_ORG')
influxdb_bucket = os.getenv('INFLUXDB_BUCKET')
# Defining the link loss
LINK_LOSS=float(os.getenv('LINK_LOSS', '0.0'))

# Enables sflow monitoring on OVS Switches
# exec(open('sflow.py').read())

# Initialize InfluxDB client
# influxdb_client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
# influxdb_write_api = influxdb_client.write_api(write_options=WriteOptions(batch_size=1))


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
        self.addLink(g1_sw1, g1_sw2, bw=99, loss=LINK_LOSS)    # l_1
        self.addLink(g1_sw2, g1_sw3, bw=96, loss=LINK_LOSS)    # l_2
        self.addLink(g1_sw1, g1_sw3, bw=100, loss=LINK_LOSS)   # l_3
        
        # Connect switches within group g2
        self.addLink(g2_sw4, g2_sw5, bw=93, loss=LINK_LOSS)    # l_4
        self.addLink(g2_sw5, g2_sw6, bw=100, loss=LINK_LOSS)   # l_5
        self.addLink(g2_sw4, g2_sw6, bw=95, loss=LINK_LOSS)    # l_6
        
        # Connect switches within group g3
        self.addLink(g3_sw7, g3_sw8, bw=89, loss=LINK_LOSS)    # l_7
        self.addLink(g3_sw8, g3_sw9, bw=91, loss=LINK_LOSS)    # l_8
        self.addLink(g3_sw7, g3_sw9, bw=97, loss=LINK_LOSS)    # l_9

        # Connect each group via links
        # g1 to g2
        self.addLink(g1_sw3, g2_sw4, bw=100)    # l_10
        # g2 to g3
        self.addLink(g2_sw5, g3_sw9, bw=100)    # l_11

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
    net.start()
    info("*** Network is running. \n")
    info("*** Running Mininet CLI\n")
    CLI(net)  # Start the mininet command line interface
    net.stop()  # Stop the network when done
    

if __name__ == '__main__':
    runNetwork()
