import os, sys
import docker

client = docker.from_env()
images = client.images.list()

presence_array = []
components = ["udr", "udm", "ausf", "nrf", "amf", "smf", "spgwu-tiny", "upf-vpp"]


for image in images:
    for component in components:
        if(str(image) == "<Image: 'soldera21/oai-" + component + ":v1.5.1'>"):
            presence_array.append(True)

if len(presence_array) != 8:
    print("********* In order to download all docker images you must login into docker *************")
    os.system("/bin/bash -c \"docker login\"")
    for component in components:
        f = open("dockerfile/Dockerfile." + component, "w")
        f.write(    "#syntax=docker/dockerfile:1\n" +
                    f"FROM oaisoftwarealliance/oai-{component}:v1.5.1\n" +
                    "RUN apt-get update\n" +
                    "RUN apt-get install iproute2 -y\n")
        f.close()

        command = "docker build -f dockerfile/Dockerfile." + component + " -t soldera21/oai-" + component + ":v1.5.1 ."
        
        os.system("/bin/bash -c \"" + command + "\"") 
else:
    print("All Docker Images are already present.")
