#!/usr/bin/env python3

import os
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import Intf
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import customClass

# exec(open('sflow.py').read())

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
        self.addLink(g1_sw1, g1_sw2)
        self.addLink(g1_sw2, g1_sw3)
        self.addLink(g1_sw1, g1_sw3)
        
        # Connect switches within group g2
        self.addLink(g2_sw4, g2_sw5)
        self.addLink(g2_sw5, g2_sw6)
        self.addLink(g2_sw4, g2_sw6)
        
        # Connect switches within group g3
        self.addLink(g3_sw7, g3_sw8)
        self.addLink(g3_sw8, g3_sw9)
        self.addLink(g3_sw7, g3_sw9)

        # Connect each group via links
        # g1 to g2
        self.addLink(g1_sw3, g2_sw4)
        # g2 to g3
        self.addLink(g2_sw5, g3_sw9)

        # Add hosts and connect to specific switches
        host1 = self.addHost('h1')  # Host in group g1
        host2 = self.addHost('h2')  # Host in group g3

        # Connect hosts to the switches
        self.addLink(host1, g1_sw1)
        self.addLink(host2, g3_sw8)

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
        info("Creating veth pair for %s\n" % host)
        os.system( 'ip link add root-%s type veth peer name %s-root' % (host, host) )
        os.system( 'ip link set root-%s up' % host )
        os.system( 'ip addr add %s dev root-%s' % (vm_ip, host) )
        os.system( 'ip route add %s dev root-%s' % (internal_ip, host) )

def add_external_interfaces(host_names, net):
    for host in host_names:
        info("*** Adding interface to root namespace for host %s\n" % host)
        iface_name = host + '-root'
        _intf = Intf( iface_name, net.get(host))

def enable_sflow(net):
    info("*** Enabling sFlow:\n")
    sflow = 'ovs-vsctl -- --id=@sflow create sflow agent=%s target=%s sampling=%s polling=%s --' % ('enp8s0','127.0.0.1',10,10)
    for s in net.switches:
      sflow += ' -- set bridge %s sflow=@sflow' % s
    info(' '.join([s.name for s in net.switches]) + "\n")
    os.system(sflow)

def runNetwork():
    setLogLevel('info')      # Set the logging level
    topo = CustomTopology()  # Create the topology
    net = Mininet(topo=topo, switch=OVSSwitch, build=False)  # Set up the network

    # Adding External controller
    c0 = net.addController(name='c0', controller=RemoteController, ip='localhost', protocol='tcp',port=6653)

    # Connect switches to Controller
    for switch in net.switches:
        switch.start([c0])

    # Build the network (to get access to hosts)
    # net.build()

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

    enable_sflow(net)

    net.start()
    print("Network is running.")
    CLI(net)  # Start the mininet command line interface
    net.stop()  # Stop the network when done

    info( '*** Deleting old virtual ethernet pairs\n' )
    delete_veth_pairs(host_names)

if __name__ == '__main__':
    runNetwork()
