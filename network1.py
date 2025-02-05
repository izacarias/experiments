#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

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


def runNetwork():
    setLogLevel('info')  # Set the logging level
    topo = CustomTopology()  # Create the topology
    net = Mininet(topo=topo, switch=OVSSwitch, build=False)  # Set up the network

    # Adding External controller
    c0 = net.addController(name='c0', controller=RemoteController, ip='localhost', protocol='tcp',port=6653)

    net.start()

    # Connect switches to Controller
    for switch in net.switches:
        switch.start([c0])

    print("Network is running.")
    CLI(net)  # Start the mininet command line interface
    net.stop()  # Stop the network when done


if __name__ == '__main__':
    runNetwork()