#!/usr/bin/env python3
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, AccessPoint
from mn_wifi.cli import CLI  # if you want interactive CLI
from containernet.node import DockerHost
from containernet.link import TCLink
from mininet.node import RemoteController

def run_topology():
    # Create a Mininet_wifi instance with Docker capabilities
    # NOTE: Because Containernet is an extension of Mininet, you might need a special fork or class
    # that merges them. If your environment merges them by default, you can do:
    net = Mininet_wifi(
        controller=RemoteController,
        link=TCLink,
        # If your environment requires a special 'switch' or 'accessPoint' class, adapt here
    )

    info("*** Creating Wi-Fi stations\n")
    sta1 = net.addStation('sta1', position='10,20,0')  # station with Wi-Fi
    sta2 = net.addStation('sta2', position='15,25,0')

    info("*** Creating AP\n")
    ap1 = net.addAccessPoint('ap1', ssid="ssid-foo", mode="g", channel="1",
                             position='10,10,0')

    info("*** Creating a normal OVS switch\n")
    s1 = net.addSwitch('s1')  # for wired connections or bridging

    info("*** Creating Docker-based hosts/servers\n")
    # Suppose we want to run an Ubuntu container that acts as a server
    # "dimage" can be e.g. "ubuntu:latest" or your custom image
    d1 = net.addDockerHost(
        'd1',
        dimage="ubuntu:latest",
        docker_args={"cpus": "0.5"},  # optional constraints
    )
    d2 = net.addDockerHost(
        'd2',
        dimage="ubuntu:latest"
    )

    info("*** Creating Controller\n")
    c0 = net.addController('c0', controller=RemoteController,
                           ip='127.0.0.1', port=6653)

    info("*** Configuring Wi-Fi\n")
    net.configureWifiNodes()  # This method sets up AP <-> station links

    info("*** Creating links\n")
    # Link the AP to the switch
    net.addLink(ap1, s1)

    # Link the Docker hosts to the switch
    net.addLink(d1, s1)
    net.addLink(d2, s1)

    info("*** Starting network\n")
    net.start()

    # At this point:
    #  - sta1, sta2 should be connected to ap1 via Wi-Fi
    #  - ap1 is connected to s1
    #  - d1, d2 are connected to s1
    #  - c0 is controlling everything remotely (127.0.0.1:6653)

    info("*** Checking connectivity\n")
    # Example: test ping
    net.pingAll()

    info("*** Dropping to CLI (optional)\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_topology()
