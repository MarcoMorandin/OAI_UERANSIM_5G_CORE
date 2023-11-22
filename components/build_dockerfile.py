import os, sys

components = ["udr", "udm", "ausf", "nrf", "amf", "smf", "spgwu-tiny", "upf-vpp"]

for component in components:
    f = open("dockerfile/Dockerfile." + component, "w")
    f.write(    "#syntax=docker/dockerfile:1\n" +
                f"FROM oaisoftwarealliance/oai-{component}:v1.5.1\n" +
                "RUN apt-get update\n" +
                "RUN apt-get install iproute2 -y\n")
    f.close()

    command = "docker build -f dockerfile/Dockerfile." + component + " -t soldera21/oai-" + component + ":v1.5.1 ."
    
    os.system("/bin/bash -c \"" + command + "\"") 

