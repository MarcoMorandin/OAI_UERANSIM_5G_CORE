#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# docker rm $(docker ps -a -f status=exited -q)
# docker exec oai-ext-dn ping -c 4 12.1.1.2

import os

from comnetsemu.cli import CLI, spawnXtermDocker
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import Controller

import json, time

if __name__ == "__main__":

    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    setLogLevel("info")

    prj_folder="."

    env = dict()

    net = Containernet(controller=Controller, link=TCLink)

    

    info("*** Add controller\n")
    net.addController("c0")

    info("*** Adding switch\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")

    '''info("*** Adding links\n")
    net.addLink(s1,  s2, bw=1000, delay="10ms", intfName1="s1-s2",  intfName2="s2-s1")
    net.addLink(s2,  s3, bw=1000, delay="50ms", intfName1="s2-s3",  intfName2="s3-s2")
    
    net.addLink(cp,      s3, bw=1000, delay="1ms", intfName1="cp-s1",  intfName2="s1-cp")
    net.addLink(upf_cld, s3, bw=1000, delay="1ms", intfName1="upf-s3",  intfName2="s3-upf_cld")
    net.addLink(upf_mec, s2, bw=1000, delay="1ms", intfName1="upf_mec-s2", intfName2="s2-upf_mec")

    net.addLink(ue,  s1, bw=1000, delay="1ms", intfName1="ue-s1",  intfName2="s1-ue")
    net.addLink(gnb, s1, bw=1000, delay="1ms", intfName1="gnb-s1", intfName2="s1-gnb")'''

    info("\n*** Starting network\n")
    net.start()

    if not AUTOTEST_MODE:
        # spawnXtermDocker("open5gs")
        # spawnXtermDocker("gnb")
        CLI(net)

    net.stop()
