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

    ipam_pool = docker.types.IPAMPool(subnet='192.168.80.0/24')
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    oai_net = client.networks.create(
        "mysql-net",
        driver="bridge",
        ipam=ipam_config,
        options={
            "com.docker.network.bridge.name": "mysql-net",
        }
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

    info("\n*** Adding mysql container\n")
    # mysql = net.addMysqlHost(
    #     "mysql",
    #     dimage="mysql:8.0",
    #     docker_args={
    #         "volumes": {
    #             prj_folder + "/database/oai_db.sql": {
    #                 "bind": "/docker-entrypoint-initdb.d/oai_db.sql",
    #                 "mode": "rw",
    #             },
    #             prj_folder + "/healthscripts/mysql-healthcheck.sh": {
    #                 "bind": "/tmp/mysql-healthcheck.sh",
    #                 "mode": "rw",
    #             },
    #         },
    #         "environment": {
    #             "TZ": "Europe/Paris",
    #             "MYSQL_DATABASE": "oai_db",
    #             "MYSQL_USER": "test",
    #             "MYSQL_PASSWORD": "test",
    #             "MYSQL_ROOT_PASSWORD": "linux",
    #         },
    #         "healthcheck": {
    #             "test": "/bin/bash -c \"/tmp/mysql-healthcheck.sh\"",
    #             "interval": 10000000000,
    #             "timeout": 5000000000,
    #             "retries": 30,
    #         },
    #         # "ports": {
    #         #     "3306/tcp": 3306,
    #         #     "33060/tcp": 33060,
    #         # },
    #     },
    # )
    cmd = "/bin/bash -c 'docker run --privileged --name mysql -v " + prj_folder + '/database/oai_db.sql:/docker-entrypoint-initdb.d/oai_db.sql:rw -v ' + prj_folder + "/healthscripts/mysql-healthcheck.sh:/tmp/mysql-healthcheck.sh:rw -e TZ=Europe/Paris -e MYSQL_DATABASE=oai_db -e MYSQL_USER=test -e MYSQL_PASSWORD=test -e MYSQL_ROOT_PASSWORD=linux --health-cmd=\"/bin/bash -c /tmp/mysql-healthcheck.sh\" --health-interval=10s --health-timeout=5s --health-retries=30 -d mysql:8.0'"
    os.system(cmd)
    oai_net.connect("mysql", ipv4_address="192.168.80.131")

    info("\n*** Adding NRF container\n")
    nrf = net.addDockerHost(
        "oai-nrf",
        dimage="networking2/oai-nrf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "NRF_INTERFACE_NAME_FOR_SBI": "nrf-s3",
                # The default HTTP2 port is 8080 for all network functions
                # It is shown here as example.
                # If you wish to change, you have to specify it for each NF
                "NRF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
            },
        },
    )
    net.addLink(nrf, s3, bw=1000, delay="1ms", intfName1="nrf-s3", intfName2="s3-nrf", params1={'ip': '192.168.70.136/24'})
    time.sleep(0.5)
    client.containers.get("oai-nrf").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o\"", detach=True)

    info("\n*** Adding NSSF container\n")
    nssf = net.addDockerHost(
        "oai-nssf",
        dimage="networking2/oai-nssf:v1.5.1",
        docker_args={
            # "privileged": True,
            "volumes": {
                prj_folder + "/nssf_slice_config.yaml": {
                    "bind": "/openair-nssf/etc/nssf_slice_config.yaml",
                    "mode": "rw",
                },
            },
            "environment": {
                "TZ": "Europe/Paris",
                "NSSF_NAME": "oai-nssf",
                "NSSF_FQDN": "nssf.oai-5gcn.eur",
                "SBI_IF_NAME": "nssf-s3",
                "SBI_PORT_HTTP2": "8080",
                "SBI_API_VERSION": "v1",
                # NSSF is not registered to NRF
                "NSSF_SLICE_CONFIG": "/openair-nssf/etc/nssf_slice_config.yaml",
            },
            "cap_add": ["NET_ADMIN", "SYS_ADMIN"],
            "cap_drop": ["ALL"],
            # "ports": {
            #     "80/tcp": 80,
            #     "8080/tcp": 8080,
            # },
        },
    )
    net.addLink(nssf, s3, bw=1000, delay="1ms", intfName1="nssf-s3", intfName2="s3-nssf", params1={'ip': '192.168.70.132/24'})
    time.sleep(0.5)
    client.containers.get("oai-nssf").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o\"", detach=True)

    info("\n*** Adding UDR container\n")
    udr = net.addDockerHost(
        "oai-udr",
        dimage="networking2/oai-udr:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "UDR_NAME": "oai-udr",
                "UDR_INTERFACE_NAME_FOR_NUDR": "udr-s3",
                "MYSQL_IPV4_ADDRESS": "192.168.80.131",
                "MYSQL_USER": "test",
                "MYSQL_PASS": "test",
                "MYSQL_DB": "oai_db",
                "WAIT_MYSQL": "120",
                "USE_FQDN_DNS": "no",
                "REGISTER_NRF": "yes",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "oai-nrf",
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "NRF_PORT": "8080",
            },
        }
    )
    net.addLink(udr, s3, bw=1000, delay="1ms", intfName1="udr-s3", intfName2="s3-udr", params1={'ip': '192.168.70.133/24'})
    time.sleep(0.5)
    client.containers.get("oai-udr").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o > /log.txt\"", detach=True)
    oai_net.connect("oai-udr", ipv4_address="192.168.80.132")

    info("\n*** Adding UDM container\n")
    udm = net.addDockerHost(
        "oai-udm",
        dimage="networking2/oai-udm:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "UDM_NAME": "oai-udm",
                "SBI_IF_NAME": "udm-s3",
                "USE_FQDN_DNS": "no",
                # UDM is not registered to NRF
                "UDR_IP_ADDRESS": "192.168.70.133",
                "UDR_PORT": "8080",
                "UDR_FQDN": "oai-udr",
                "REGISTER_NRF": "yes",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "oai-nrf",
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "NRF_PORT": "8080",
            },
        },
    )
    net.addLink(udm, s3, bw=1000, delay="1ms", intfName1="udm-s3", intfName2="s3-udm", params1={'ip': '192.168.70.134/24'})
    time.sleep(0.5)
    client.containers.get("oai-udm").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o\"", detach=True)

    info("\n*** Adding AUSF container\n")
    ausf = net.addDockerHost(
        "oai-ausf",
        dimage="networking2/oai-ausf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "AUSF_NAME": "oai-ausf",
                "SBI_IF_NAME": "ausf-s3",
                "USE_FQDN_DNS": "no",
                # UDM is not registered to NRF
                "UDM_IP_ADDRESS": "192.168.70.134",
                "UDM_FQDN": "oai-udm",
                "REGISTER_NRF": "yes",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "oai-nrf",
                # changes for HTTP2
                "USE_HTTP2": "yes",
                "UDM_PORT": "8080",
                "NRF_PORT": "8080",
            },
        },
    )
    net.addLink(ausf, s3, bw=1000, delay="1ms", intfName1="ausf-s3", intfName2="s3-ausf", params1={'ip': '192.168.70.135/24'})
    time.sleep(0.5)
    client.containers.get("oai-ausf").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o\"", detach=True)
    
    info("\n*** Adding AMF container\n")
    amf = net.addDockerHost(
        "oai-amf",
        dimage="networking2/oai-amf:v1.5.1",
        docker_args={
            "environment": {
                "TZ":"Europe/Paris",
                "MCC":"208",
                "MNC":"95",
                "REGION_ID":"128",
                "AMF_SET_ID":"1",
                "SERVED_GUAMI_MCC_0":"208",
                "SERVED_GUAMI_MNC_0":"95",
                "SERVED_GUAMI_REGION_ID_0":"128",
                "SERVED_GUAMI_AMF_SET_ID_0":"1",
                "PLMN_SUPPORT_MCC":"208",
                "PLMN_SUPPORT_MNC":"95",
                "PLMN_SUPPORT_TAC":"0xa000",
                "SST_0":"128",
                "SD_0":"128",
                "AMF_INTERFACE_NAME_FOR_NGAP":"amf-s3",
                "AMF_INTERFACE_NAME_FOR_N11":"amf-s3",
                "SMF_INSTANCE_ID_0":"1",
                "SMF_FQDN_0":"oai-smf",
                "SMF_IPV4_ADDR_0":"192.168.70.139",
                "SELECTED_0":"true",
                "NF_REGISTRATION":"yes",
                "USE_FQDN_DNS":"no",
                "SMF_SELECTION":"yes",
                "EXTERNAL_AUSF":"yes",
                "EXTERNAL_UDM":"yes",
                "EXTERNAL_NSSF":"no",
                "NRF_IPV4_ADDRESS":"192.168.70.136",
                "NRF_FQDN":"oai-nrf",
                "AUSF_IPV4_ADDRESS":"192.168.70.135",
                "AUSF_FQDN":"oai-ausf",
                "UDM_IPV4_ADDRESS":"192.168.70.134",
                "UDM_FQDN":"oai-udm",
                "USE_HTTP2":"yes",
                "NRF_PORT":"8080",
                "AUSF_PORT":"8080",
                "UDM_PORT":"8080",
            },
        },
    )
    net.addLink(amf, s3, bw=1000, delay="1ms", intfName1="amf-s3", intfName2="s3-amf", params1={'ip': '192.168.70.138/24'})
    time.sleep(0.5)
    client.containers.get("oai-amf").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o\"", detach=True)

    info("\n*** Adding SMF container\n")
    smf = net.addDockerHost(
        "oai-smf",
        dimage="networking2/oai-smf:v1.5.1",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "SMF_INTERFACE_NAME_FOR_N4": "smf-s3",
                "SMF_INTERFACE_NAME_FOR_SBI": "smf-s3",
                "SMF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
                "DEFAULT_DNS_IPV4_ADDRESS": "172.17.0.1",
                "DEFAULT_DNS_SEC_IPV4_ADDRESS": "8.8.8.8",
                "AMF_IPV4_ADDRESS": "192.168.70.138",
                "AMF_FQDN": "oai-amf",
                # "UDM_IPV4_ADDRESS": "192.168.70.134",
                # "UDM_FQDN": "oai-udm",
                "UPF_IPV4_ADDRESS": "192.168.70.142",
                "UPF_FQDN_0": "oai-spgwu",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "oai-nrf",
                "USE_LOCAL_SUBSCRIPTION_INFO": "yes",
                "REGISTER_NRF": "yes",
                "DISCOVER_UPF": "yes",
                "DISCOVER_PCF": "no",
                "USE_LOCAL_SUBSCRIPTION_INFO": "yes",
                "USE_LOCAL_PCC_RULES": "yes",
                "USE_FQDN_DNS": "no",
                # One single slice is defined.
                "DNN_NI0": "oai",
                "TYPE0": "IPv4",
                "DNN_RANGE0": "12.2.1.2 - 12.2.1.254",
                "NSSAI_SST0": "128",
                "NSSAI_SD0": "128",
                "SESSION_AMBR_UL0": "50Mbps",
                "SESSION_AMBR_DL0": "100Mbps",
                # changes for HTTP2
                "HTTP_VERSION": "2",
                "AMF_PORT": "8080",
                # "UDM_PORT": "8080",
                "NRF_PORT": "8080",
                "UE_MTU": "1500",
            },
        },
    )
    net.addLink(smf, s3, bw=1000, delay="1ms", intfName1="smf-s3", intfName2="s3-smf", params1={'ip': '192.168.70.139/24'})
    time.sleep(0.5)
    client.containers.get("oai-smf").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_${CONTAINER_NAME} -c /openair-${CONTAINER_NAME}/etc/${CONTAINER_NAME}.conf -o\"", detach=True)

    info("*** Adding SPGWU-UPF container\n")
    spgwu = net.addDockerHost(
        "oai-spgwu",
        dimage="networking2/oai-spgwu-tiny:v1.5.1",
        docker_args={
            # "privileged": True,
            "environment": {
                "TZ": "Europe/Paris",
                "SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP": "spgwu-s2",
                "SGW_INTERFACE_NAME_FOR_SX": "spgwu-s2",
                "PGW_INTERFACE_NAME_FOR_SGI": "spgwu-s2",
                "NETWORK_UE_NAT_OPTION": "yes",
                "NETWORK_UE_IP": "12.2.1.0/24",
                "ENABLE_5G_FEATURES": "yes",
                "REGISTER_NRF": "yes",
                # "USE_FQDN_NRF": "yes",
                # "UPF_FQDN_5G": "oai-spgwu",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_API_VERSION": "v1",
                # "NRF_FQDN": "oai-nrf",
                # Mandatory to set the NRF PORT to 8080 (it is set to default to 80 otherwise)
                "HTTP_VERSION": "2",
                "NRF_PORT": "8080",
                # One single slice / DNN is defined
                "NSSAI_SST_0": "128",
                "NSSAI_SD_0": "128",
                "DNN_0": "default",
            },
        }
    )
    net.addLink(spgwu, s2, bw=1000, delay="1ms", intfName1="spgwu-s2", intfName2="s2-spgwu", params1={'ip': '192.168.70.142/24'})
    time.sleep(0.5)
    client.containers.get("oai-spgwu").exec_run("/bin/bash -c \"/openair-${CONTAINER_NAME}/bin/oai_spgwu -c /openair-${CONTAINER_NAME}/etc/spgw_u.conf -o\"", detach=True)

    info("\n*** Adding EXT-DN container\n")
    ext_dn = net.addDockerHost(
        "oai-ext-dn",
        dimage="oaisoftwarealliance/trf-gen-cn5g:latest",
        docker_args={
            # "privileged": True,
            # "init": True,
            # "entrypoint": "/bin/bash -c \"iptables -t nat -A POSTROUTING -o ext_dn-s3 -j MASQUERADE; ip route add 12.2.1.0/24 via 192.168.70.142 dev ext_dn-s3;\"",
            "command": ["/bin/bash", "-c", "trap : SIGTERM SIGINT; sleep infinity & wait"],
            "healthcheck": {
                "test": "/bin/bash -c \"iptables -L -t nat | grep MASQUERADE\"",
                "interval": 10000000000,
                "timeout": 5000000000,
                "retries": 10,
            },
        },
    )
    net.addLink(ext_dn, s3, bw=1000, delay="50ms", intfName1="ext_dn-s3", intfName2="s3-ext_dn", params1={'ip': '192.168.70.145/24'})
    time.sleep(0.5)
    client.containers.get("oai-ext-dn").exec_run("/bin/bash -c \"iptables -t nat -A POSTROUTING -o ext_dn-s3 -j MASQUERADE; ip route add 12.2.1.0/24 via 192.168.70.142 dev ext_dn-s3;\"")
    # # ??? ^^^ 12.2.1.0/24

    # info("\n*** Adding gNB\n")
    # gnb = net.addDockerHost(
    #     "gnb", 
    #     dimage="networking2/ueransim:3.2.6",
    #     dcmd="bash /mnt/ueransim/gnb_init.sh",
    #     docker_args={
    #         "volumes": {
    #             prj_folder + "/ueransim/config": {
    #                 "bind": "/mnt/ueransim",
    #                 "mode": "rw",
    #             },
    #             prj_folder + "/log": {
    #                 "bind": "/mnt/log",
    #                 "mode": "rw",
    #             },
    #             "/etc/timezone": {
    #                 "bind": "/etc/timezone",
    #                 "mode": "ro",
    #             },
    #             "/etc/localtime": {
    #                 "bind": "/etc/localtime",
    #                 "mode": "ro",
    #             },
    #             "/dev": {
    #                 "bind": "/dev",
    #                 "mode": "rw"
    #             },
    #         },
    #     },
    # )

    # info("\n*** Adding UE\n")
    # ue = net.addDockerHost(
    #     "ue", 
    #     dimage="networking2/ueransim:3.2.6",
    #     dcmd="bash /mnt/ueransim/ue_init.sh",
    #     docker_args={
    #         "volumes": {
    #             prj_folder + "/ueransim/config": {
    #                 "bind": "/mnt/ueransim",
    #                 "mode": "rw",
    #             },
    #             prj_folder + "/log": {
    #                 "bind": "/mnt/log",
    #                 "mode": "rw",
    #             },
    #             "/etc/timezone": {
    #                 "bind": "/etc/timezone",
    #                 "mode": "ro",
    #             },
    #             "/etc/localtime": {
    #                 "bind": "/etc/localtime",
    #                 "mode": "ro",
    #             },
    #             "/dev": {"bind": "/dev", "mode": "rw"},
    #         },
    #     },
    # )
    
    # net.addLink(ue,  s1, bw=1000, delay="1ms", intfName1="ue-s1",  intfName2="s1-ue", params1={'ip': '192.168.70.153/24'})
    # net.addLink(gnb, s1, bw=1000, delay="1ms", intfName1="gnb-s1", intfName2="s1-gnb", params1={'ip': '192.168.70.152/24'})

    info("\n*** Starting network\n")
    net.start()

    if not AUTOTEST_MODE:
        CLI(net)
    
    oai_net.disconnect("mysql")
    oai_net.disconnect("oai-udr")

    net.delLink(s1s2_link)
    net.delLink(s2s3_link)

    net.stop()

    oai_net.remove()
    
    os.system("/bin/bash -c \"docker kill mysql\"")
    os.system("/bin/bash -c \"docker rm mysql\"")
