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

#TODO Aggiungere script per pullare tutte le immagini
#TODO Aggiungere script per controllare tipo di architettura usata, nel caso arm fa partire: docker run --rm --privileged aptman/qus -s -- -p x86_64

AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

setLogLevel("info")

client = docker.from_env()
containers = client.containers

prj_folder = os.getcwd()

net = Containernet(controller=Controller, link=TCLink)
mgr = VNFManager(net)

remove_containers()

info("*** Add controller\n")
net.addController("c0")

info("*** Adding switch\n")
s3 = net.addSwitch("s1")

mysql = net.addDockerHost(
    "mysql",
    dimage="dev_test",
    ip="192.168.70.131",
    docker_args={
        "hostname" : "mysql"
    }
)
net.addLink(mysql, s3, bw=1000, delay="1ms", intfName1="mysql-s3", intfName2="s3-mysql", params1={'ip': '192.168.70.131/24'})

nrf = net.addDockerHost(
    "nrf",
    dimage="dev_test",
    ip="192.168.70.136",
    docker_args={
        "hostname" : "nrf"
    }
)
net.addLink(nrf, s3, bw=1000, delay="1ms", intfName1="nrf-s3", intfName2="s3-nrf", params1={'ip': '192.168.70.136/24'})

nssf = net.addDockerHost(
    "nssf",
    dimage="dev_test",
    ip="192.168.70.132",
    docker_args={
        "hostname" : "nssf"
    }
)
net.addLink(nssf, s3, bw=1000, delay="1ms", intfName1="nssf-s3", intfName2="s3-nssf", params1={'ip': '192.168.70.132/24'})

udr = net.addDockerHost(
    "udr",
    dimage="dev_test",
    ip="192.168.70.133",
    docker_args={
        "hostname" : "udr"
    }
)
net.addLink(udr, s3, bw=1000, delay="1ms", intfName1="udr-s3", intfName2="s3-udr", params1={'ip': '192.168.70.133/24'})

udm = net.addDockerHost(
    "udm",
    dimage="dev_test",
    ip="192.168.70.134",
    docker_args={
        "hostname" : "udm"
    }
)
net.addLink(udm, s3, bw=1000, delay="1ms", intfName1="udm-s3", intfName2="s3-udm", params1={'ip': '192.168.70.134/24'})

ausf = net.addDockerHost(
    "ausf",
    dimage="dev_test",
    ip="192.168.70.135",
    docker_args={
        "hostname" : "ausf"
    }
)
net.addLink(ausf, s3, bw=1000, delay="1ms", intfName1="ausf-s3", intfName2="s3-ausf", params1={'ip': '192.168.70.135/24'})


amf = net.addDockerHost(
    "amf",
    dimage="dev_test",
    ip="192.168.70.138",
    docker_args={
        "hostname" : "amf"
    }
)
net.addLink(amf, s3, bw=1000, delay="1ms", intfName1="amf-s3", intfName2="s3-amf", params1={'ip': '192.168.70.138/24'})


smf = net.addDockerHost(
    "smf",
    dimage="dev_test",
    ip="192.168.70.139",
    docker_args={
        "hostname" : "smf"
    }
)
net.addLink(smf, s3, bw=1000, delay="1ms", intfName1="smf-s3", intfName2="s3-smf", params1={'ip': '192.168.70.139/24'})

ext_dn = net.addDockerHost(
    "ext_dn",
    dimage="dev_test",
    docker_args={
        "hostname" : "ext_dn"
    }
)
net.addLink(ext_dn, s3, bw=1000, delay="50ms", intfName1="ext_dn-s3", intfName2="s3-ext_dn", params1={'ip': '192.168.70.145/24'})

net.start()

mysql_srv = mgr.addContainer(
    name = "mysql_srv",
    dhost = "mysql",
    dimage = "mysql:8.0",
    dcmd = "",
    docker_args={
        "volumes": {
            prj_folder + "/database/oai_db.sql": {
                "bind": "/docker-entrypoint-initdb.d/oai_db.sql",
                "mode": "rw",
            },
            prj_folder + "/healthscripts/mysql-healthcheck.sh": {
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
    }
)

nrf_srv = mgr.addContainer(
    name = "nrf_srv",
    dhost = "nrf",
    dimage = "oaisoftwarealliance/oai-nrf:v1.5.1",
    dcmd = "",
    docker_args={
        "environment": {
            "TZ": "Europe/Paris",
            "NRF_INTERFACE_NAME_FOR_SBI": "nrf-s3",
            # The default HTTP2 port is 8080 for all network functions
            # It is shown here as example.
            # If you wish to change, you have to specify it for each NF
            "NRF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
        },
    }
)

nssf_srv = mgr.addContainer(
    name = "nssf_srv",
    dhost = "nssf",
    dimage = "oaisoftwarealliance/oai-nssf:v1.5.1",
    dcmd = "",
    docker_args={
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
    }
)

udr_srv = mgr.addContainer(
    name = "udr_srv",
    dhost = "udr",
    dimage = "oaisoftwarealliance/oai-udr:v1.5.1",
    dcmd = "",
    docker_args={
        "environment": {
            "TZ": "Europe/Paris",
            "UDR_NAME": "oai-udr",
            "UDR_INTERFACE_NAME_FOR_NUDR": "udr-s3",
            "MYSQL_IPV4_ADDRESS": "192.168.70.131",
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

udm_srv = mgr.addContainer(
    name = "udm_srv",
    dhost = "udm",
    dimage = "oaisoftwarealliance/oai-udm:v1.5.1",
    dcmd = "",
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
    }
)

ausf_srv = mgr.addContainer(
    name = "ausf_srv",
    dhost = "ausf",
    dimage = "oaisoftwarealliance/oai-ausf:v1.5.1",
    dcmd = "",
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
    }
)

amf_srv = mgr.addContainer(
    name = "amf_srv",
    dhost = "amf",
    dimage = "oaisoftwarealliance/oai-amf:v1.5.1",
    dcmd = "",
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
    }
)

smf_srv = mgr.addContainer(
    name = "smf_srv",
    dhost = "smf",
    dimage = "oaisoftwarealliance/oai-smf:v1.5.1",
    dcmd = "",
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
    }
)

ext_dn_srv = mgr.addContainer(
    name = "ext_dn_srv",
    dhost = "ext_dn",
    dimage = "oaisoftwarealliance/trf-gen-cn5g:latest",
    dcmd = "",
    docker_args={
        "entrypoint": "/bin/bash -c \"iptables -t nat -A POSTROUTING -o ext_dn-s3 -j MASQUERADE; ip route add 12.2.1.0/24 via 192.168.70.142 dev ext_dn-s3; ip route; sleep infinity\"",
        "command": ["/bin/bash", "-c", "trap : SIGTERM SIGINT; sleep infinity & wait"],
        "healthcheck": {
            "test": "/bin/bash -c \"iptables -L -t nat | grep MASQUERADE\"",
            "interval": 10000000000,
            "timeout": 5000000000,
            "retries": 10,
        },
        "privileged": True,
    }
)

if not AUTOTEST_MODE:
    CLI(net)

mgr.removeContainer("mysql_srv")
mgr.removeContainer("nrf_srv")
mgr.removeContainer("nssf_srv")
mgr.removeContainer("udr_srv")
mgr.removeContainer("udm_srv")
mgr.removeContainer("ausf_srv")
mgr.removeContainer("amf_srv")
mgr.removeContainer("smf_srv")
mgr.removeContainer("ext_dn_srv")

net.stop()
mgr.stop()