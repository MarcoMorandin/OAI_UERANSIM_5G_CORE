import os, sys
import docker

def build_images(basedir = "./"):
    presence_array = []
    mysql_presence = False
    components = ["udr", "udm", "ausf", "nrf", "amf", "smf", "spgwu-tiny", "upf-vpp"]

    client = docker.from_env()
    images = client.images.list()

    for image in images:
        for component in components:
            if(str(image) == "<Image: 'networking2/oai-" + component + ":v1.5.1'>"):
                presence_array.append(True)
        if(str(image) ==  "<Image: 'networking2/mysql-net:8.0'>" ):
            mysql_presence = True

    if(len(presence_array) != len(components) or mysql_presence is False):
        print("********* Some required images are missed *********")
        print("********* Now downloading and rebuilding all required images *********")
        print("********* In order to download all docker images you must login to DockerHub *********")
        os.system("/bin/bash -c \"docker login\"")
        for component in components:
            print(f"********* Downloading and rebuilding of oai-{component} image ************")
            f = open(basedir + "dockerfile/Dockerfile." + component, "w")
            f.write(    "#syntax=docker/dockerfile:1\n" +
                        f"FROM oaisoftwarealliance/oai-{component}:v1.5.1\n" +
                        "RUN apt-get update\n" +
                        "RUN apt-get install -y --no-install-recommends iproute2 tcpdump iputils-ping iperf3\n" +
                        "RUN apt-get autoremove -y && apt-get autoclean\n")
            f.close()

            image = client.images.build(path=basedir + "dockerfile/", dockerfile="Dockerfile." + component, tag="networking2/oai-" + component + ":v1.5.1", rm=True)
            print(f"********* FINISHED Downloading and rebuilding of oai-{component} *********")
        if(mysql_presence is False):
            print(f"********* Downloading and rebuilding of mysql image ************")
            image = client.images.build(path=basedir + "mysql-net/", dockerfile="Dockerfile.debian", tag="networking2/mysql-net:8.0", rm=True)
            print(f"********* FINISHED Downloading and rebuilding of mysql *********")
        
    else:
        print("********* All Docker Images are already present *********")
