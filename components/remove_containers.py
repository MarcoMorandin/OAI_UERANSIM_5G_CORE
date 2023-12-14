import os, sys
import docker

from mininet.log import info, setLogLevel


def remove_containers():
    client = docker.from_env()
    containers = client.containers
    for container in containers.list():
        # remove also exited and networks...
        if("dev_test" in str(container.image) or "mysql" in str(container.image) or "oaisoftwarealliance" in str(container.image)):
            container.remove(force = True)

    info("*** All project containers have been killed\n")
