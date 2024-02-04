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

#TODO Modificare script per pullare tutte le immagini e rimuovere i container anche usciti e le reti
#TODO get_images() docker login


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
        mgr.removeContainer("smf_srv")
        mgr.removeContainer("upf_srv")
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


    smf = net.addDockerHost(
        "smf",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "smf",
        },
    )
    net.addLink(smf, s3, bw=1000, delay="1ms", intfName1="smf-s3", intfName2="s3-smf", params1={'ip': '192.168.70.139/24'})

    upf = net.addDockerHost(
        "upf",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "upf",
        },
    )
    net.addLink(upf, s2, bw=1000, delay="1ms")
    net.addLink(upf, s2, bw=1000, delay="1ms", intfName1="upf-s2-2", intfName2="s2-upf-2", params1={'ip': '192.168.72.201/24'})
    net.addLink(upf, s2, bw=1000, delay="1ms", intfName1="upf-s2-3", intfName2="s2-upf-3", params1={'ip': '192.168.73.201/24'})
    # net.addLink(spgwu, s2, bw=1000, delay="1ms")

    ext_dn = net.addDockerHost(
        "ext_dn",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "ext_dn",
        },
    )
    net.addLink(ext_dn, s3, bw=1000, delay="50ms", intfName1="ext_dn-s3", intfName2="s3-ext_dn", params1={'ip': '192.168.73.145/24'})

    gnb = net.addDockerHost(
        "gnb",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "gnb",
        },
    )
    net.addLink(gnb, s3, bw=1000, delay="50ms", intfName1="gnb-s3", intfName2="s3-gnb", params1={'ip': '192.168.70.152/24'})

    ue = net.addDockerHost(
        "ue",
        dimage="marcomorandin/dev_test",
        docker_args={
            "hostname" : "ue",
        },
    )
    net.addLink(ue, s3, bw=1000, delay="50ms", intfName1="ue-s3", intfName2="s3-ue", params1={'ip': '192.168.70.153/24'})

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

    info("*** Adding SMF container\n")
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
                "AMF_FQDN": "amf_srv",
                # "UDM_IPV4_ADDRESS": "192.168.70.134",
                # "UDM_FQDN": "oai-udm",
                "UPF_IPV4_ADDRESS": "192.168.70.201",
                "UPF_FQDN_0": "upf_srv",
                "NRF_IPV4_ADDRESS": "192.168.70.136",
                "NRF_FQDN": "nrf_srv",
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

    info("*** Adding UPF container\n")
    upf_srv = mgr.addContainer(
        name="upf_srv",
        dhost = "upf",
        dimage="oaisoftwarealliance/oai-upf-vpp:v1.5.1",
        dcmd = "",
        docker_args={
            "environment": {
                "IF_1_IP": "192.168.70.201",
                "IF_1_TYPE": "N4",
                "IF_1_IP_REMOTE": "192.168.70.139", # SMF IP Address
                "IF_2_IP": "192.168.72.201",
                "IF_2_TYPE": "N3",
                "IF_2_NWI": "access.oai.org",
                "IF_3_IP": "192.168.73.201",
                "IF_3_TYPE": "N6",
                "IF_3_IP_REMOTE": "192.168.73.145", # EXT-DN IP Address
                "IF_3_NWI": "internet.oai.org",
                "NAME": "VPP-UPF",
                "MNC": "95",
                "MCC": "208",
                "REALM": "3gppnetwork.org",
                "VPP_MAIN_CORE": "0",
                "VPP_CORE_WORKER": "1",
    #           VPP_PLUGIN_PATH=/usr/lib64/vpp_plugins/                # RHEL7
                "VPP_PLUGIN_PATH": "/usr/lib/x86_64-linux-gnu/vpp_plugins/", # Ubntu18.04
                "SNSSAI_SD": "123",
                "SNSSAI_SST": "222",
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
            "entrypoint": "/bin/bash -c \"iptables -t nat -A POSTROUTING -o ext_dn-s3 -j MASQUERADE; ip route add 12.2.1.2/32 via 192.168.73.201 dev ext_dn-s3; ip route; sleep infinity\"",
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
    gnb_srv = mgr.addContainer(
        name = "gnb_srv", 
        dimage="oaisoftwarealliance/oai-gnb:develop",
        dhost = "gnb",
        dcmd="",
        docker_args={
            "privileged": True,
            "environment": {
                "USE_ADDITIONAL_OPTIONS": "--sa -E --rfsim --log_config.global_log_options level,nocolor,time",
                "ASAN_OPTIONS": "detect_leaks=0",
            },
            "volumes": {
                prj_folder + "/ran/gnb-du.sa.band78.106prb.rfsim.conf": {
                    "bind": "/opt/oai-gnb/etc/gnb.conf",
                    "mode": "rw",
                },
            },
            "healthcheck": {
                "test": "/bin/bash -c \"pgrep nr-softmodem\"",
                "interval": 10000000000,
                "timeout": 5000000000,
                "retries": 10,
            },
        },
    )

    info("*** Adding UE\n")
    ue_srv = mgr.addContainer(
        name = "ue_srv", 
        dimage="oaisoftwarealliance/oai-nr-ue:develop",
        dhost = "ue",
        dcmd="",
        docker_args={
            "privileged": True,
            "environment": {
                "USE_ADDITIONAL_OPTIONS": "USE_ADDITIONAL_OPTIONS: -E --sa --rfsim -r 106 --numerology 1 --uicc0.imsi 208990100001101 -C 3619200000 --rfsimulator.serveraddr 192.168.70.152 --log_config.global_log_options level,nocolor,time",
            },
            "volumes": {
                prj_folder + "/ran/nrue.uicc.conf": {
                    "bind": "/opt/oai-nr-ue/etc/nr-ue.conf",
                    "mode": "rw",
                },
            },
            "healthcheck": {
                "test": "/bin/bash -c \"pgrep nr-uesoftmodem\"",
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
            client.containers.get("amf_srv").attrs["State"]["Health"]["Status"] != "healthy" or
            client.containers.get("smf_srv").attrs["State"]["Health"]["Status"] != "healthy" 
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