import os, sys
import docker
import subprocess

def build_images(basedir = "./"):
    
    presence_array = []
    base_tag = "networking2/"
    components = [  "oai-udr:v1.5.1",
                    "oai-udm:v1.5.1",
                    "oai-ausf:v1.5.1",
                    "oai-nrf:v1.5.1",
                    "oai-amf:v1.5.1",
                    "oai-smf:v1.5.1",
                    "oai-spgwu-tiny:v1.5.1",
                    "oai-upf-vpp:v1.5.1",
                    "mysql-net:8.0",
                    "ueransim:3.2.6"]

    components = [(base_tag + component) for component in components]

    client = docker.from_env()
    images = client.images.list()

    images = [image.tags[0] for image in images]

    components = list(set(components).difference(images))

    if len(components):
        print("********* Some required images are missed *********")
        print("********* Now downloading and rebuilding all required images *********")
        login = subprocess.check_output("docker system info | grep -E 'Username|Registry'", shell=True).decode("utf-8")
        if "Username" not in login:
            print("********* In order to download all docker images you must login to DockerHub *********")
            os.system("/bin/bash -c \"docker login\"")
        for component in components:
            tmp = component.replace("networking2/", "")
            print(f"********* Downloading and rebuilding of {tmp} image ************")
            if("oai" in component):
                f = open(basedir + "dockerfile/Dockerfile." + tmp, "w")
                f.write(    "#syntax=docker/dockerfile:1\n" +
                            f"FROM oaisoftwarealliance/{tmp}\n" +
                            "RUN apt-get update\n" +
                            "RUN apt-get install -y --no-install-recommends iproute2 tcpdump iputils-ping iperf3\n" +
                            "RUN apt-get autoremove -y && apt-get autoclean\n")
                f.close()
                image = client.images.build(path=basedir + "dockerfile/", dockerfile="Dockerfile." + tmp, tag=component, rm=True)
            if("mysql" in component):
                image = client.images.build(path=basedir + "mysql-net/", dockerfile="Dockerfile.debian", tag=component, rm=True)
            if("ueransim" in component):
                client.images.pull(repository="rfed/myueransim_v3-2-6")
                os.system("/bin/bash -c \"docker tag rfed/myueransim_v3-2-6  networking2/ueransim:3.2.6 && docker rmi rfed/myueransim_v3-2-6\"")
            print(f"********* FINISHED Downloading and rebuilding of {tmp} *********")    
    else:
        print("********* All Docker Images are already present *********")
