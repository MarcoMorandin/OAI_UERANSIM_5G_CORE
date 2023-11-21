#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# docker rm $(docker ps -a -f status=exited -q)
# docker exec oai-ext-dn ping -c 4 12.1.1.2
# docker network prune

import os

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink, Intf
from mininet.log import info, setLogLevel
from mininet.node import Controller
import docker

import json, time

if __name__ == "__main__":

    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    setLogLevel("info")
    env = dict()

    client = docker.from_env()

    prj_folder = os.getcwd()

    net = Containernet(controller=Controller, link=TCLink)
    ipam_pool = docker.types.IPAMPool(subnet='192.168.80.0/24')
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    oai_net = client.networks.create(
        "oai-public-net",
        driver="bridge",
        ipam=ipam_config,
        options={
            "com.docker.network.bridge.name": "oai_net",
        }
    )

    info("*** Adding mysql container\n")
    mysql = net.addDockerHost(
        "mysql",
        dimage="mysql:8.0",
        docker_args={
            "volumes": {
                prj_folder + "/database/oai_db.sql": {
                    "bind": "/docker-entrypoint-initdb.d/oai_db.sql",
                    "mode": "rw",
                },
                prj_folder + "/healthscripts/mysql-healthcheck2.sh": {
                    "bind": "/tmp/mysql-healthcheck.sh",
                    "mode": "rw",
                },
            },
            "environment": {
                "TZ": "Europe/Paris",
                "MYSQL_DATABASE": "oai_db",
                "MYSQL_USER": "test",
                "MYSQL_PASSWORD": "test",
                "MYSQL_ROOT_PASSWORD": "linux",
            },
            "healthcheck": {
                "test": "/bin/bash -c \"/tmp/mysql-healthcheck.sh\"",
                "interval": 10000000000,
                "timeout": 5000000000,
                "retries": 30,
            },
            "ports": { "3306/tcp": 3306 },
        },
    )
    oai_net.connect("mysql", ipv4_address="192.168.80.131")

    '''info("*** Adding UDR container\n")
    udr = net.addDockerHost(
        "oai-udr",
        dimage="oaisoftwarealliance/oai-udr:v1.5.1",
        docker_args={
            "volumes": {
                prj_folder + "/database/oai_db.sql": {
                    "bind": "/docker-entrypoint-initdb.d/oai_db.sql",
                    "mode": "rw",
                },
                prj_folder + "/healthscripts/mysql-healthcheck2.sh": {
                    "bind": "/tmp/mysql-healthcheck.sh",
                    "mode": "rw",
                },
            },
            "environment": {
                "TZ": "Europe/Paris",
                "UDR_NAME": "OAI_UDR",
                "UDR_INTERFACE_NAME_FOR_NUDR": "eth0",
                "MYSQL_IPV4_ADDRESS": "192.168.70.131",
                "MYSQL_USER": "test",
                "MYSQL_PASS": "test",
                "MYSQL_DB": "oai_db",
                "WAIT_MYSQL": "120",
                "USE_HTTP2": "yes",
                "UDR_INTERFACE_HTTP2_PORT_FOR_NUDR": "8080",
            },
            "healthcheck": {
                "test": "/bin/bash -c \"/tmp/mysql-healthcheck.sh\"",
                "interval": 10000000000,
                "timeout": 5000000000,
                "retries": 30,
            },
            "ports": { "80/tcp": 3306, "8080/tcp": 8080 },
        },
    )'''

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
        CLI(net)

    oai_net.disconnect("mysql")

    net.stop()
    oai_net.remove()
