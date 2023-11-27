import os, sys
import docker


presence_array = []
components = ["udr", "udm", "ausf", "nrf", "amf", "smf", "spgwu-tiny", "upf-vpp"]

client = docker.from_env()
images = client.images.list()

for image in images:
    for component in components:
        if(str(image) == "<Image: 'networking2/oai-" + component + ":v1.5.1'>"):
            presence_array.append(True)

if len(presence_array) != 8:
    print("********* Some required images are missed *********")
    print("********* Now this script download and rebuild all the required images *********")
    print("********* In order to download all docker images you must login into docker *********")
    os.system("/bin/bash -c \"docker login\"")
    for component in components:
        print(f"********* Downloading and rebuilding of oai-{component} image ************")
        f = open("dockerfile/Dockerfile." + component, "w")
        f.write(    "#syntax=docker/dockerfile:1\n" +
                    f"FROM oaisoftwarealliance/oai-{component}:v1.5.1\n" +
                    "RUN apt-get update\n" +
                    "RUN apt-get install iproute2 -y\n")
        f.close()

        image, build_logs = client.images.build(path="dockerfile/", dockerfile="Dockerfile." + component, tag="networking2/oai-" + component + ":v1.5.1", rm=True)
        print(f"********* Downloading and rebuilding of oai-{component} finished *********")

else:
    print("********* All Docker Images are already present. *********")
