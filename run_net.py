#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# docker rm $(docker ps -a -f status=exited -q)
# docker kill $(docker ps -a)
# docker exec oai-ext-dn ping -c 4 12.1.1.2
# docker network prune
# docker rmi $(docker images)
# ip link delete s1-s2

import os
import docker
import time

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink, Intf
from mininet.log import info, setLogLevel
from mininet.node import Controller
from components.build_dockerfile import *
from components.remove_containers import *

import json, time

if __name__ == "__main__":
    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)
    
    setLogLevel("info")

    client = docker.from_env()
    containers = client.containers

    prj_folder = os.getcwd()

    net = Containernet(controller=Controller, link=TCLink)
    
    remove_containers()

    build_images(basedir="./components/")

    
    info("*** Adding mysql container\n")
    mysql = net.addDockerHost(
        "mysql",
        dimage="networking2/mysql-net:8.0",
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
            # "ports": {
            #     "3306/tcp": 3306,
            # },
        },
    )

    info("*** Adding UDR container\n")
    udr = net.addDockerHost(
        "oai-udr",
        dimage="networking2/oai-udr:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "UDR_NAME": "OAI-UDR",
                "UDR_INTERFACE_NAME_FOR_NUDR": "eth0",
                "MYSQL_IPV4_ADDRESS": "192.168.70.131",
                "MYSQL_USER": "test",
                "MYSQL_PASS": "test",
                "MYSQL_DB": "oai_db",
                "WAIT_MYSQL": "120",
                # UDR is not registered to NRF
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "UDR_INTERFACE_HTTP2_PORT_FOR_NUDR": "8080",
            },
            # "ports": {
            #     "80/tcp": 80,
            #     "8080/tcp": 8080,
            # },
        },
    )

    info("*** Adding UDM container\n")
    udm = net.addDockerHost(
        "oai-udm",
        dimage="networking2/oai-udm:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "UDM_NAME": "OAI-UDM",
                "SBI_IF_NAME": "eth0",
                "USE_FQDN_DNS": "yes",
                # UDM is not registered to NRF
                "UDR_IP_ADDRESS": "192.168.70.133",
                "UDR_VERSION_NB": "v1",
                "UDR_FQDN": "oai-udr",
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "SBI_HTTP2_PORT": "8080",
                "UDR_PORT": "8080",
            },
            # "ports": {
            #     "80/tcp": 80,
            #     "8080/tcp": 8080,
            # },
        },
    )

    info("*** Adding AUSF container\n")
    ausf = net.addDockerHost(
        "oai-ausf",
        dimage="networking2/oai-ausf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "AUSF_NAME": "OAI-AUSF",
                "SBI_IF_NAME": "eth0",
                "USE_FQDN_DNS": "yes",
                # UDM is not registered to NRF
                "UDM_IP_ADDRESS": "192.168.70.134",
                "UDM_VERSION_NB": "v1",
                "UDM_FQDN": "oai-udm",
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "UDM_PORT": "8080",
            },
            # "ports": {
            #     "80/tcp": 80,
            #     "8080/tcp": 8080,
            # },
        },
    )

    info("*** Adding NRF container\n")
    nrf = net.addDockerHost(
        "oai-nrf",
        dimage="networking2/oai-nrf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "NRF_INTERFACE_NAME_FOR_SBI": "eth0",
                # The default HTTP2 port is 8080 for all network functions
                # It is shown here as example.
                # If you wish to change, you have to specify it for each NF
                "NRF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
            },
            # "ports": {
            #     "80/tcp": 80,
            #     "8080/tcp": 8080,
            # },
        },
    )

    info("*** Adding AMF container\n")
    amf = net.addDockerHost(
        "oai-amf",
        dimage="networking2/oai-amf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "MCC": "208",
                "MNC": "95",
                "REGION_ID": "128",
                "AMF_SET_ID": "1",
                "SERVED_GUAMI_MCC_0": "208",
                "SERVED_GUAMI_MNC_0": "95",
                "SERVED_GUAMI_REGION_ID_0": "128",
                "SERVED_GUAMI_AMF_SET_ID_0": "1",
                "SERVED_GUAMI_MCC_1": "460",
                "SERVED_GUAMI_MNC_1": "11",
                "SERVED_GUAMI_REGION_ID_1": "10",
                "SERVED_GUAMI_AMF_SET_ID_1": "1",
                "PLMN_SUPPORT_MCC": "208",
                "PLMN_SUPPORT_MNC": "95",
                "PLMN_SUPPORT_TAC": "0xa000",
                # Slice 0 (128, 128)
                "SST_0": "128",
                "SD_0": "128",
                # End Slice 0
                "AMF_INTERFACE_NAME_FOR_NGAP": "eth0",
                "AMF_INTERFACE_NAME_FOR_N11": "eth0",
                # First SMF instance
                "SMF_INSTANCE_ID_0": "1",
                "SMF_FQDN_0": "oai-smf",
                "SMF_HTTP_VERSION_0": "v1",
                "SELECTED_0": "true",
                # Feature list
                "EXTERNAL_NRF": "no",
                "NRF_SELECTION": "yes",
                "SMF_SELECTION": "yes",
                "USE_FQDN_DNS": "yes",
                "EXTERNAL_AUSF": "yes",
                "EXTERNAL_NSSF": "yes",
                "INT_ALGO_LIST": "[\"NIA1\" , \"NIA2\"]",
                "CIPH_ALGO_LIST": "[\"NEA1\" , \"NEA2\"]",
                # Other NF
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "oai-nrf",
                "AUSF_IPV4_ADDRESS": "192.168.70.135",
                "AUSF_FQDN": "oai-ausf",
                "UDM_IPV4_ADDRESS": "192.168.70.134",
                "UDM_FQDN": "oai-udm",
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "NRF_PORT": "8080",
                "AUSF_PORT": "8080",
                "UDM_PORT": "8080",
            },
            "ports": {
                "80/tcp": 80,
                "8080/tcp": 8080,
                "38412/sctp": 38412,
            },
        },
    )

    info("*** Adding SMF container\n")
    smf = net.addDockerHost(
        "oai-smf",
        dimage="networking2/oai-smf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "SMF_INTERFACE_NAME_FOR_N4": "eth0",
                "SMF_INTERFACE_NAME_FOR_SBI": "eth0",
                "SMF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
                "DEFAULT_DNS_IPV4_ADDRESS": "172.21.3.100",
                "DEFAULT_DNS_SEC_IPV4_ADDRESS": "8.8.8.8",
                "AMF_IPV4_ADDRESS": "192.168.70.138",
                "AMF_FQDN": "oai-amf",
                "UDM_IPV4_ADDRESS": "192.168.70.134",
                "UDM_FQDN": "oai-udm",
                "UPF_IPV4_ADDRESS": "127.0.0.1",
                "UPF_FQDN_0": "localhost",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "oai-nrf",
                "REGISTER_NRF": "yes",
                "DISCOVER_UPF": "yes",
                "DISCOVER_PCF": "no",
                "USE_LOCAL_SUBSCRIPTION_INFO": "yes",
                "USE_LOCAL_PCC_RULES": "yes",
                "USE_FQDN_DNS": "yes",
                # One single slice is defined.
                "DNN_NI0": "default",
                "TYPE0": "IPv4",
                "DNN_RANGE0": "12.2.1.2 - 12.2.1.128",
                "NSSAI_SST0": "128",
                "NSSAI_SD0": "128",
                "SESSION_AMBR_UL0": "50Mbps",
                "SESSION_AMBR_DL0": "100Mbps",
                # changes for HTTP2
                "HTTP_VERSION": "2",
                "AMF_PORT": "8080",
                "UDM_PORT": "8080",
                "NRF_PORT": "8080",
            },
            # "ports": {
            #     "80/tcp": 80,
            #     "8080/tcp": 8080,
            #     "8805/udp": 8805,
            # },
        },
    )

    info("*** Adding SPGWU-UPF container\n")
    spgwu = net.addDockerHost(
        "oai-spgwu",
        dimage="networking2/oai-spgwu-tiny:v1.5.1",
        docker_args={
            # "privileged": True,
            "environment": {
                "TZ": "Europe/Paris",
                "SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP": "eth0",
                "SGW_INTERFACE_NAME_FOR_SX": "eth0",
                "PGW_INTERFACE_NAME_FOR_SGI": "eth0",
                "NETWORK_UE_NAT_OPTION": "yes",
                "NETWORK_UE_IP": "12.2.1.0/24",
                "ENABLE_5G_FEATURES": "yes",
                "REGISTER_NRF": "yes",
                "USE_FQDN_NRF": "yes",
                "UPF_FQDN_5G": "oai-spgwu",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_API_VERSION": "v1",
                "NRF_FQDN": "oai-nrf",
                # Mandatory to set the NRF PORT to 8080 (it is set to default to 80 otherwise)
                "HTTP_VERSION": "2",
                "NRF_PORT": "8080",
                # One single slice / DNN is defined
                "NSSAI_SST_0": "128",
                "NSSAI_SD_0": "128",
                "DNN_0": "default",
            },
            "cap_add": ["NET_ADMIN", "SYS_ADMIN"],
            "cap_drop": ["ALL"],
            # "ports": {
            #     "8080/tcp": 8080,
            #     "2152/udp": 2152,
            #     "8805/udp": 8805,
            # },
        },
    )

    info("*** Adding EXT-DN container\n")
    ext_dn = net.addDockerHost(
        "oai-ext-dn",
        dimage="oaisoftwarealliance/trf-gen-cn5g:latest",
        docker_args={
            # "privileged": True,
            # "init": True,
            "command": ["/bin/bash", "-c", "trap : SIGTERM SIGINT; sleep infinity & wait"],
            "healthcheck": {
                "test": "/bin/bash -c \"iptables -L -t nat | grep MASQUERADE\"",
                "interval": 10000000000,
                "timeout": 5000000000,
                "retries": 10,
            },
        },
    )

    time.sleep(20)

    info("*** Adding gNB\n")
    gnb = net.addDockerHost(
        "gnb", 
        dimage="networking2/ueransim:3.2.6",
        dcmd="bash /mnt/ueransim/gnb_init.sh",
        docker_args={
            "volumes": {
                prj_folder + "/ueransim/config": {
                    "bind": "/mnt/ueransim",
                    "mode": "rw",
                },
                prj_folder + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
                "/dev": {
                    "bind": "/dev",
                    "mode": "rw"
                },
            },
            "cap_add": ["NET_ADMIN"],
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    info("*** Adding UE\n")
    ue = net.addDockerHost(
        "ue", 
        dimage="networking2/ueransim:3.2.6",

        dcmd="bash /mnt/ueransim/ue_init.sh",
        docker_args={
            "volumes": {
                prj_folder + "/ueransim/config": {
                    "bind": "/mnt/ueransim",
                    "mode": "rw",
                },
                prj_folder + "/log": {
                    "bind": "/mnt/log",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
                "/dev": {"bind": "/dev", "mode": "rw"},
            },
            "cap_add": ["NET_ADMIN"],
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )


    info("*** Add controller\n")
    net.addController("c0")

    info("*** Adding switch\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")

    info("*** Adding links\n")
    s1s2_link = net.addLink(s1,  s2, bw=1000, delay="10ms", intfName1="s1-s2",  intfName2="s2-s1")
    s2s3_link = net.addLink(s2,  s3, bw=1000, delay="50ms", intfName1="s2-s3",  intfName2="s3-s2")

    net.addLink(mysql, s3, bw=1000, delay="1ms", intfName1="mysql-s3", intfName2="s3-mysql", params1={'ip': '192.168.70.131/24'})
    net.addLink(udr, s3, bw=1000, delay="1ms", intfName1="udr-s3", intfName2="s3-udr", params1={'ip': '192.168.70.133/24'})
    net.addLink(udm, s3, bw=1000, delay="1ms", intfName1="udm-s3", intfName2="s3-udm", params1={'ip': '192.168.70.134/24'})
    net.addLink(ausf, s3, bw=1000, delay="1ms", intfName1="ausf-s3", intfName2="s3-ausf", params1={'ip': '192.168.70.135/24'})
    net.addLink(nrf, s3, bw=1000, delay="1ms", intfName1="nrf-s3", intfName2="s3-nrf", params1={'ip': '192.168.70.136/24'})
    net.addLink(amf, s3, bw=1000, delay="1ms", intfName1="amf-s3", intfName2="s3-amf", params1={'ip': '192.168.70.138/24'})
    net.addLink(smf, s3, bw=1000, delay="1ms", intfName1="smf-s3", intfName2="s3-smf", params1={'ip': '192.168.70.139/24'})
    net.addLink(spgwu, s2, bw=1000, delay="1ms", intfName1="spgwu-s2", intfName2="s2-spgwu", params1={'ip': '192.168.70.142/24'})
    net.addLink(ext_dn, s3, bw=1000, delay="50ms", intfName1="ext_dn-s3", intfName2="s3-ext_dn", params1={'ip': '192.168.70.145/24'})
    
    net.addLink(ue,  s1, bw=1000, delay="1ms", intfName1="ue-s1",  intfName2="s1-ue", params1={'ip': '192.168.70.153/24'})
    net.addLink(gnb, s1, bw=1000, delay="1ms", intfName1="gnb-s1", intfName2="s1-gnb", params1={'ip': '192.168.70.152/24'})

    client.containers.get("oai-ext-dn").exec_run("/bin/bash -c \"iptables -t nat -A POSTROUTING -o ext_dn-s3 -j MASQUERADE; ip route add 12.2.1.2/32 via 192.168.70.142 dev ext_dn-s3;\"")

    info("\n*** Starting network\n")
    net.start()

    if not AUTOTEST_MODE:
        CLI(net)

    net.delLink(s1s2_link)
    net.delLink(s2s3_link)

    net.stop()
    
