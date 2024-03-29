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
        # "oaisoftwarealliance/oai-pcf:v1.5.1",
        # "oaisoftwarealliance/oai-spgwu-tiny:v1.5.1",
        "oaisoftwarealliance/oai-upf-vpp:v1.5.1",
        "rohankharade/ueransim:latest",
        "mysql:8.0",
        "marcomorandin/trf-gen-cn5g:v1.5.1",
        "marcomorandin/dev_test:latest",
        "oaisoftwarealliance/oai-nr-ue:develop",
        "oaisoftwarealliance/oai-gnb:develop",
    ]

    client = docker.from_env()
    images = client.images.list()
    images = [image.tags[0] for image in images]

    components = list(set(components).difference(images))

    if len(components):
        info("***Some required images are missing, now downloading\n")
        for component in components:
            output = subprocess.check_output(f"docker pull {component}", shell=True).decode("utf-8")
            info(output)
            if "Error response" in output:
                raise Exception(f"ERROR downloading {component}, now exiting. Maybe \"docker login\" is needed")
            info(f"*** FINISHED downloading of {component}\n")    
    else:
        info("*** All Docker Images are already present\n")
