import os, sys
import docker
import subprocess

from mininet.log import info, setLogLevel

setLogLevel("info")

def get_images():
    components = [  
        "oaisoftwarealliance/oai-nssf:v1.5.1",
        "oaisoftwarealliance/oai-udr:v1.5.1",
        "oaisoftwarealliance/oai-udm:v1.5.1",
        "oaisoftwarealliance/oai-ausf:v1.5.1",
        "oaisoftwarealliance/oai-nrf:v1.5.1",
        "oaisoftwarealliance/oai-amf:v1.5.1",
        "oaisoftwarealliance/oai-smf:v1.5.1",
        "oaisoftwarealliance/oai-pcf:v1.5.1",
        "oaisoftwarealliance/oai-spgwu-tiny:v1.5.1",
        "oaisoftwarealliance/oai-upf-vpp:v1.5.1",
        "oaisoftwarealliance/trf-gen-cn5g:latest",
        "rohankharade/ueransim:latest",
        "mysql:8.0",
        "marcomorandin/trf-gen-cn5g:v1.5.1"
    ]

    client = docker.from_env()
    images = client.images.list()
    images = [image.tags[0] for image in images]

    components = list(set(components).difference(images))

    if len(components):
        print("********* Some required images are missing, now downloading *********")
        for component in components:
            output = subprocess.check_output(f"docker pull {component}", shell=True).decode("utf-8")
            info(output)
            if "Error response" in output:
                raise Exception(f"ERROR downloading {component}, now exiting. Maybe \"docker login\" is needed")
            print(f"********* FINISHED downloading of {component} *********")    
    else:
        print("********* All Docker Images are already present *********")
