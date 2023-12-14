import os
import docker
import time
import subprocess


from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink, Intf
from mininet.log import info, setLogLevel
from mininet.node import Controller
from components.get_images import *
from components.remove_containers import *

import time

#DOCS -> come scegliere elementi comuni del network slicing 
# https://www.scirp.org/journal/paperinformation?paperid=110977#ref22

AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

setLogLevel("info")

client = docker.from_env()
containers = client.containers

prj_folder = os.getcwd()
wait_timeout = 150

net = Containernet(controller=Controller, link=TCLink)
mgr = VNFManager(net)

def stop_network():
    try: 
        mgr.removeContainer("mysql_srv")
        mgr.removeContainer("nrf_srv")
        mgr.removeContainer("nssf_srv")
        mgr.removeContainer("udr_srv")
        mgr.removeContainer("udm_srv")
        mgr.removeContainer("ausf_srv")
        mgr.removeContainer("amf_srv")
        mgr.removeContainer("smf_slice1_srv")
        mgr.removeContainer("smf_slice2_srv")
        mgr.removeContainer("smf_slice3_srv")
        mgr.removeContainer("upf_slice1_srv")
        mgr.removeContainer("upf_slice2_srv")
        mgr.removeContainer("upf_slice3_srv")
        mgr.removeContainer("ext_dn_srv")
        mgr.removeContainer("ueransim_srv")
    except ValueError:
        pass
    net.delLink(s1s2_link)
    net.delLink(s2s3_link)

    net.stop()
    mgr.stop()

remove_containers()

try:

    if(os.uname()[4] == "aarch64"):
        info("*** It looks like you are using arm architecture\n")
        info("*** Install and run QEMU for emulating amd64 containers\n")
        os.system("docker run --rm --privileged aptman/qus -s -- -p x86_64 >/dev/null 2>&1")

    try:
        get_images()
        pass
    except Exception as error:
        info("Error downloading, now exiting. Maybe \"docker login\" is needed\n")
        net.stop()
        mgr.stop()
        exit()

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding switches\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")

    s1s2_link = net.addLink(s1,  s2, bw=1000, delay="10ms", intfName1="s1-s2",  intfName2="s2-s1")
    s2s3_link = net.addLink(s2,  s3, bw=1000, delay="50ms", intfName1="s2-s3",  intfName2="s3-s2")
    info("\n")

    info("*** Adding dev_tests\n")

    mysql = net.addDockerHost(
        "mysql",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "mysql",
        },
    )
    net.addLink(mysql, s3, bw=1000, delay="1ms", intfName1="mysql-s3", intfName2="s3-mysql", params1={'ip': '192.168.70.131/24'})

    nrf = net.addDockerHost(
        "nrf",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "nrf",
        },
    )
    net.addLink(nrf, s3, bw=1000, delay="1ms", intfName1="nrf-s3", intfName2="s3-nrf", params1={'ip': '192.168.70.136/24'})

    nssf = net.addDockerHost(
        "nssf",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "nssf",
        },
    )
    net.addLink(nssf, s3, bw=1000, delay="1ms", intfName1="nssf-s3", intfName2="s3-nssf", params1={'ip': '192.168.70.132/24'})

    udr = net.addDockerHost(
        "udr",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "udr",
        },
    )
    net.addLink(udr, s3, bw=1000, delay="1ms", intfName1="udr-s3", intfName2="s3-udr", params1={'ip': '192.168.70.133/24'})

    udm = net.addDockerHost(
        "udm",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "udm",
        },
    )
    net.addLink(udm, s3, bw=1000, delay="1ms", intfName1="udm-s3", intfName2="s3-udm", params1={'ip': '192.168.70.134/24'})

    ausf = net.addDockerHost(
        "ausf",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "ausf",
        },
    )
    net.addLink(ausf, s3, bw=1000, delay="1ms", intfName1="ausf-s3", intfName2="s3-ausf", params1={'ip': '192.168.70.135/24'})


    amf = net.addDockerHost(
        "amf",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "amf",
        },
    )
    net.addLink(amf, s3, bw=1000, delay="1ms", intfName1="amf-s3", intfName2="s3-amf", params1={'ip': '192.168.70.138/24'})

    # Slice 1
    smf_slice1 = net.addDockerHost(
        "smf_slice1",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "smf_slice1",
        },
    )
    net.addLink(smf_slice1, s3, bw=1000, delay="1ms", intfName1="smf-slice1-s3", intfName2="s3-smf-slice1", params1={'ip': '192.168.70.152/24'})

    upf_slice1 = net.addDockerHost(
        "upf_slice1",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "upf_slice1",
        },
    )
    net.addLink(upf_slice1, s2, bw=1000, delay="1ms")
    net.addLink(upf_slice1, s2, bw=1000, delay="1ms", intfName1="upf-slice1-s2-2", intfName2="s2-upf-slice1-2", params1={'ip': '192.168.72.142/24'})
    net.addLink(upf_slice1, s2, bw=1000, delay="1ms", intfName1="upf-slice1-s2-3", intfName2="s2-upf-slice1-3", params1={'ip': '192.168.73.142/24'})

    # Slice 2
    smf_slice2 = net.addDockerHost(
        "smf_slice2",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "smf_slice2",
        },
    )
    net.addLink(smf_slice2, s3, bw=1000, delay="1ms", intfName1="smf-slice2-s3", intfName2="s3-smf-slice2", params1={'ip': '192.168.70.153/24'})

    upf_slice2 = net.addDockerHost(
        "upf_slice2",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "upf_slice2",
        },
    )
    net.addLink(upf_slice2, s2, bw=1000, delay="1ms")
    net.addLink(upf_slice2, s2, bw=1000, delay="1ms", intfName1="upf-slice2-s2-2", intfName2="s2-upf-slice2-2", params1={'ip': '192.168.72.143/24'})
    net.addLink(upf_slice2, s2, bw=1000, delay="1ms", intfName1="upf-slice2-s2-3", intfName2="s2-upf-slice2-3", params1={'ip': '192.168.73.143/24'})

    #Slice 3
    smf_slice3 = net.addDockerHost(
        "smf_slice3",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "smf_slice3",
        },
    )
    net.addLink(smf_slice3, s3, bw=1000, delay="1ms", intfName1="smf-slice3-s3", intfName2="s3-smf-slice3", params1={'ip': '192.168.70.154/24'})

    upf_slice3 = net.addDockerHost(
        "upf_slice3",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "upf_slice3",
        },
    )
    net.addLink(upf_slice3, s2, bw=1000, delay="1ms")
    net.addLink(upf_slice3, s2, bw=1000, delay="1ms", intfName1="upf-slice3-s2-2", intfName2="s2-upf-slice3-2", params1={'ip': '192.168.72.144/24'})
    net.addLink(upf_slice3, s2, bw=1000, delay="1ms", intfName1="upf-slice3-s2-3", intfName2="s2-upf-slice3-3", params1={'ip': '192.168.73.144/24'})

    ext_dn = net.addDockerHost(
        "ext_dn",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "ext_dn",
        },
    )
    net.addLink(ext_dn, s3, bw=1000, delay="50ms", intfName1="ext_dn-s3", intfName2="s3-ext_dn", params1={'ip': '192.168.73.145/24'})

    ueransim = net.addDockerHost(
        "ueransim",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "ueransim",
        },
    )
    net.addLink(ueransim, s3, bw=1000, delay="50ms", intfName1="ueransim-s3", intfName2="s3-ueransim", params1={'ip': '192.168.70.152/24'})

    net.start()

    info("*** Adding mysql container\n")
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

    elapsed = 0
    info("Waiting for mysql to be up and healthy")
    while client.containers.get("mysql_srv").attrs["State"]["Health"]["Status"] != "healthy":
        time.sleep(0.5)
        info(".")
        elapsed += 1
        if elapsed >= wait_timeout:
            info("\n")
            mgr.removeContainer("mysql_srv")
            net.delLink(s1s2_link)
            net.delLink(s2s3_link)
            net.stop()
            mgr.stop()
            info("Error timeout reached. Exiting\n")
            exit()
    info("\n")

    info("*** Adding NRF container\n")
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

    info("*** Adding NSSF container\n")
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
                "NSSF_NAME": "nssf_srv",
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

    info("*** Adding UDR container\n")
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

    info("*** Adding UDM container\n")
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

    info("*** Adding AUSF container\n")
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

    info("*** Adding AMF container\n")
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
                # Slice 0
                "SST_0":"128",
                "SD_0":"128",
                # Slice 1
                "SST_1":"1",
                "SD_1":"1",
                # Slice 2
                "SST_2":"130",
                "SD_2":"130",
                # First SMF
                "SMF_INSTANCE_ID_0":"1",
                "SMF_FQDN_0":"smf_slice1_srv",
                "SMF_HTTP_VERSION_0":"v1",
                "SELECTED_0":"true",
                "SMF_IPV4_ADDR_0":"192.168.70.152",
                # Second SMF
                "SMF_INSTANCE_ID_1":"2",
                "SMF_FQDN_1":"smf_slice2_srv",
                "SMF_HTTP_VERSION_1":"v1",
                "SELECTED_1":"true",
                "SMF_IPV4_ADDR_1":"192.168.70.153", 
                # Third SMF
                "SMF_INSTANCE_ID_2":"3",
                "SMF_FQDN_2":"smf_slice3_srv",
                "SMF_HTTP_VERSION_2":"v1",
                "SELECTED_2":"true",
                "SMF_IPV4_ADDR_2":"192.168.70.154", 

                "AMF_INTERFACE_NAME_FOR_NGAP":"amf-s3",
                "AMF_INTERFACE_NAME_FOR_N11":"amf-s3",
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

    info("*** Adding SMF for Slice 1 container\n")
    smf_slice1_srv = mgr.addContainer(
        name = "smf_slice1_srv",
        dhost = "smf_slice1",
        dimage = "oaisoftwarealliance/oai-smf:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "SMF_INTERFACE_NAME_FOR_N4": "smf-slice1-s3",
                "SMF_INTERFACE_NAME_FOR_SBI": "smf-slice1-s3",
                "SMF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
                "DEFAULT_DNS_IPV4_ADDRESS": "172.17.0.1",
                "DEFAULT_DNS_SEC_IPV4_ADDRESS": "8.8.8.8",
                "AMF_IPV4_ADDRESS": "192.168.70.138",
                "AMF_FQDN": "amf_srv",
                "UDM_IPV4_ADDRESS": "192.168.70.134",
                "UDM_FQDN": "udm_srv",
                # Slice 1
                "UPF_IPV4_ADDRESS": "192.168.70.142",
                "UPF_FQDN_0": "upf_slice1_srv",
                "DNN_NI0": "slice1",
                "TYPE0": "IPv4",
                "DNN_RANGE0": "12.1.1.2 - 12.1.1.254",
                "NSSAI_SST0": "128",
                "NSSAI_SD0": "128",
                #
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "nrf_srv",
                "USE_LOCAL_SUBSCRIPTION_INFO": "yes",
                "REGISTER_NRF": "yes",
                "DISCOVER_UPF": "yes",
                "DISCOVER_PCF": "no",
                "USE_LOCAL_PCC_RULES": "yes",
                "USE_FQDN_DNS": "no",
                "SESSION_AMBR_UL0": "50Mbps",
                "SESSION_AMBR_DL0": "100Mbps",
                # changes for HTTP2
                "HTTP_VERSION": "2",
                "AMF_PORT": "8080",
                "UDM_PORT": "8080",
                "NRF_PORT": "8080",
                "UE_MTU": "1500",
            },
        }
    )

    info("*** Adding SMF for Slice 2 container\n")
    smf_slice2_srv = mgr.addContainer(
        name = "smf_slice2_srv",
        dhost = "smf_slice2",
        dimage = "oaisoftwarealliance/oai-smf:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "SMF_INTERFACE_NAME_FOR_N4": "smf-slice2-s3",
                "SMF_INTERFACE_NAME_FOR_SBI": "smf-slice2-s3",
                "SMF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
                "DEFAULT_DNS_IPV4_ADDRESS": "172.17.0.1",
                "DEFAULT_DNS_SEC_IPV4_ADDRESS": "8.8.8.8",
                "AMF_IPV4_ADDRESS": "192.168.70.138",
                "AMF_FQDN": "amf_srv",
                "UDM_IPV4_ADDRESS": "192.168.70.134",
                "UDM_FQDN": "udm_srv",
                # Slice 2
                "UPF_IPV4_ADDRESS": "192.168.70.143",
                "UPF_FQDN_0": "upf_slice2_srv",
                "DNN_NI0": "slice2",
                "TYPE0": "IPv4",
                "DNN_RANGE0": "12.2.1.2 - 12.2.1.254",
                "NSSAI_SST0": "1",
                "NSSAI_SD0": "1",
                #
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "nrf_srv",
                "USE_LOCAL_SUBSCRIPTION_INFO": "yes",
                "REGISTER_NRF": "yes",
                "DISCOVER_UPF": "yes",
                "DISCOVER_PCF": "no",
                "USE_LOCAL_PCC_RULES": "yes",
                "USE_FQDN_DNS": "no",
                "SESSION_AMBR_UL0": "50Mbps",
                "SESSION_AMBR_DL0": "100Mbps",
                # changes for HTTP2
                "HTTP_VERSION": "2",
                "AMF_PORT": "8080",
                "UDM_PORT": "8080",
                "NRF_PORT": "8080",
                "UE_MTU": "1500",
            },
        }
    )


    info("*** Adding SMF for Slice 3 container\n")
    smf_slice3_srv = mgr.addContainer(
        name = "smf_slice3_srv",
        dhost = "smf_slice3",
        dimage = "oaisoftwarealliance/oai-smf:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                "TZ": "Europe/Paris",
                "SMF_INTERFACE_NAME_FOR_N4": "smf-slice3-s3",
                "SMF_INTERFACE_NAME_FOR_SBI": "smf-slice3-s3",
                "SMF_INTERFACE_HTTP2_PORT_FOR_SBI": "8080",
                "DEFAULT_DNS_IPV4_ADDRESS": "172.17.0.1",
                "DEFAULT_DNS_SEC_IPV4_ADDRESS": "8.8.8.8",
                "AMF_IPV4_ADDRESS": "192.168.70.138",
                "AMF_FQDN": "amf_srv",
                "UDM_IPV4_ADDRESS": "192.168.70.134",
                "UDM_FQDN": "udm_srv",
                # Slice 3
                "UPF_IPV4_ADDRESS": "192.168.70.144",
                "UPF_FQDN_0": "upf_slice3_srv",
                "DNN_NI0": "slice3",
                "TYPE0": "IPv4",
                "DNN_RANGE0": "12.3.1.2 - 12.3.1.254",
                "NSSAI_SST0": "1",
                "NSSAI_SD0": "1",
                #
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "nrf_srv",
                "USE_LOCAL_SUBSCRIPTION_INFO": "yes",
                "REGISTER_NRF": "yes",
                "DISCOVER_UPF": "yes",
                "DISCOVER_PCF": "no",
                "USE_LOCAL_PCC_RULES": "yes",
                "USE_FQDN_DNS": "no",
                "SESSION_AMBR_UL0": "50Mbps",
                "SESSION_AMBR_DL0": "100Mbps",
                # changes for HTTP2
                "HTTP_VERSION": "2",
                "AMF_PORT": "8080",
                "UDM_PORT": "8080",
                "NRF_PORT": "8080",
                "UE_MTU": "1500",
            },
        }
    )

    info("*** Adding UPF for Slice 1 container\n")
    upf_slice1_srv = mgr.addContainer(
        name="upf_slice1_srv",
        dhost = "upf_slice1",
        dimage="oaisoftwarealliance/oai-upf-vpp:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                # Slice 1
                "IF_1_IP": "192.168.70.142",
                "IF_1_TYPE": "N4",
                "IF_1_IP_REMOTE": "192.168.70.152", # SMF Slice 1 IP Address
                "IF_2_IP": "192.168.72.142",
                "IF_2_TYPE": "N3",
                "IF_2_NWI": "access.oai.org",
                "IF_3_IP": "192.168.73.142",
                "IF_3_TYPE": "N6",
                "IF_3_IP_REMOTE": "192.168.73.145", # EXT-DN IP Address
                "IF_3_NWI": "internet.oai.org",
                "SNSSAI_SD": "128",
                "SNSSAI_SST": "128",
                #
                "NAME": "vpp_upf_slice1_srv",
                "MNC": "95",
                "MCC": "208",
                "REALM": "3gppnetwork.org",
                "VPP_MAIN_CORE": "0",
                "VPP_CORE_WORKER": "1",
                "VPP_PLUGIN_PATH": "/usr/lib/x86_64-linux-gnu/vpp_plugins/",
                "DNN": "default",
                "REGISTER_NRF": "yes",
                "NRF_IP_ADDR": "192.168.70.136",
                #changes for HTTP2
                "NRF_PORT": "8080",
                "HTTP_VERSION": "2",
            },
            "privileged": True,
            "cap_add": ["NET_ADMIN", "SYS_ADMIN"],
            "cap_drop": ["ALL"],
        }
    )

    info("*** Adding UPF for Slice 2 container\n")
    upf_slice2_srv = mgr.addContainer(
        name="upf_slice2_srv",
        dhost = "upf_slice2",
        dimage="oaisoftwarealliance/oai-upf-vpp:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                # Slice 2
                "IF_1_IP": "192.168.70.143",
                "IF_1_TYPE": "N4",
                "IF_1_IP_REMOTE": "192.168.70.153", # SMF Slice 2 IP Address
                "IF_2_IP": "192.168.72.143",
                "IF_2_TYPE": "N3",
                "IF_2_NWI": "access.oai.org",
                "IF_3_IP": "192.168.73.143",
                "IF_3_TYPE": "N6",
                "IF_3_IP_REMOTE": "192.168.73.145", # EXT-DN IP Address
                "IF_3_NWI": "internet.oai.org",
                "SNSSAI_SD": "1",
                "SNSSAI_SST": "1",
                #
                "NAME": "vpp_upf_slice2_srv",
                "MNC": "95",
                "MCC": "208",
                "REALM": "3gppnetwork.org",
                "VPP_MAIN_CORE": "0",
                "VPP_CORE_WORKER": "1",
                "VPP_PLUGIN_PATH": "/usr/lib/x86_64-linux-gnu/vpp_plugins/",
                "DNN": "default",
                "REGISTER_NRF": "yes",
                "NRF_IP_ADDR": "192.168.70.136",
                #changes for HTTP2
                "NRF_PORT": "8080",
                "HTTP_VERSION": "2",
            },
            "privileged": True,
            "cap_add": ["NET_ADMIN", "SYS_ADMIN"],
            "cap_drop": ["ALL"],
        }
    )

    info("*** Adding UPF for Slice 3 container\n")
    upf_slice3_srv = mgr.addContainer(
        name="upf_slice3_srv",
        dhost = "upf_slice3",
        dimage="oaisoftwarealliance/oai-upf-vpp:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                # Slice 2
                "IF_1_IP": "192.168.70.144",
                "IF_1_TYPE": "N4",
                "IF_1_IP_REMOTE": "192.168.70.154", # SMF Slice 3 IP Address
                "IF_2_IP": "192.168.72.144",
                "IF_2_TYPE": "N3",
                "IF_2_NWI": "access.oai.org",
                "IF_3_IP": "192.168.73.144",
                "IF_3_TYPE": "N6",
                "IF_3_IP_REMOTE": "192.168.73.145", # EXT-DN IP Address
                "IF_3_NWI": "internet.oai.org",
                "SNSSAI_SD": "130",
                "SNSSAI_SST": "130",
                #
                "NAME": "vpp_upf_slice3_srv",
                "MNC": "95",
                "MCC": "208",
                "REALM": "3gppnetwork.org",
                "VPP_MAIN_CORE": "0",
                "VPP_CORE_WORKER": "1",
                "VPP_PLUGIN_PATH": "/usr/lib/x86_64-linux-gnu/vpp_plugins/",
                "DNN": "default",
                "REGISTER_NRF": "yes",
                "NRF_IP_ADDR": "192.168.70.136",
                #changes for HTTP2
                "NRF_PORT": "8080",
                "HTTP_VERSION": "2",
            },
            "privileged": True,
            "cap_add": ["NET_ADMIN", "SYS_ADMIN"],
            "cap_drop": ["ALL"],
        }
    )

    info("*** Adding EXT-DN container\n")
    ext_dn_srv = mgr.addContainer(
        name = "ext_dn_srv",
        dhost = "ext_dn",
        dimage = "marcomorandin/trf-gen-cn5g:v1.5.1",
        dcmd = "",
        docker_args={
            "entrypoint": "/bin/bash -c \"iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; ip route add 12.1.1.2/32 via 192.168.70.142 dev eth0; ip route add 12.2.1.2/32 via 192.168.70.143 dev eth0; ip route add 12.3.1.2/32 via 192.168.70.144 dev eth1; ip route; sleep infinity",
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

    info("*** Adding gNB\n")
    ueransim_srv = mgr.addContainer(
        name = "ueransim_srv", 
        dimage="rohankharade/ueransim:latest",
        dhost = "ueransim",
        dcmd="",
        docker_args={
            "environment": {
                # GNB Congig Parameters
                "MCC":"208",
                "MNC":"95",
                "NCI":"0x000000010",
                "TAC":"0xa000",
                "LINK_IP":"192.168.70.152",
                "NGAP_IP":"192.168.70.152",
                "GTP_IP":"192.168.70.152",
                "NGAP_PEER_IP":"192.168.70.135", # AUSF IP Address
                "SST":"128",
                "SD":"128",
                "SST_0":"128",
                "SD_0":"128",
                "SST_1":"1",
                "SD_1":"0",
                "SST_2":"131",
                "SD_2":"131",
                "IGNORE_STREAM_IDS":"true",
                # UE Config Parameters
                "NUMBER_OF_UE":"2",
                "IMSI":"208950000000035",
                "KEY":"0C0A34601D4F07677303652C0462535B",
                "OP":"63bfa50ee6523365ff14c1f45f88737d",
                "OP_TYPE":"OPC",
                "AMF_VALUE":"8000",
                "IMEI":"356938035643803",
                "IMEI_SV":"0035609204079514",
                "GNB_IP_ADDRESS":"192.168.70.152",
                "PDU_TYPE":"IPv4",
                "APN":"default",
                "SST_R":"128", #Requested N-SSAI
                "SD_R":"128",
                "SST_C":"128",
                "SD_C":"128",
                "SST_D":"128",
                "SD_D":"128",
            },
            "volumes": {
                prj_folder + "/conf/custom-gnb.yaml": {
                    "bind": "/ueransim/etc/custom-gnb.yaml",
                    "mode": "rw",
                },
                prj_folder + "/conf/custom-ue.yaml": {
                    "bind": "/ueransim/etc/custom-ue.yaml",
                    "mode": "rw",
                },
            },
            "healthcheck": {
                "test": "/bin/bash -c \"ifconfig uesimtun0\"",
                "interval": 10000000000,
                "timeout": 5000000000,
                "retries": 10,
            },
        },
    )



    elapsed = 0
    info("Waiting for all services to be up and healthy")
    while ( client.containers.get("nrf_srv").attrs["State"]["Health"]["Status"] != "healthy" or
            client.containers.get("nssf_srv").attrs["State"]["Health"]["Status"] != "healthy" or
            client.containers.get("udr_srv").attrs["State"]["Health"]["Status"] != "healthy" or
            client.containers.get("udm_srv").attrs["State"]["Health"]["Status"] != "healthy" or
            client.containers.get("ausf_srv").attrs["State"]["Health"]["Status"] != "healthy" or
            client.containers.get("amf_srv").attrs["State"]["Health"]["Status"] != "healthy"
            # or client.containers.get("smf_srv").attrs["State"]["Health"]["Status"] != "healthy" 
            # or client.containers.get("ext_dn_srv").attrs["State"]["Health"]["Status"] != "healthy" 
            ):
        time.sleep(0.5)
        info(".")
        elapsed += 1
        if elapsed >= wait_timeout:
            info("\n")
            stop_network()
            info("Error timeout reached. Exiting\n")
            exit()
    info("\n")

    info("*** All services started correctly. Net ready!\n")

    if not AUTOTEST_MODE:
        CLI(net)

    stop_network()
except Exception:
    stop_network()
except KeyboardInterrupt:
    stop_network()