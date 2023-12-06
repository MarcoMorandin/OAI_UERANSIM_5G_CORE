import os, sys
import docker

def remove_containers():
    client = docker.from_env()
    containers = client.containers
    for container in containers.list():
        if("networking2" in str(container.image) or "oaisoftwarealliance" in str(container.image)):
            container.remove(force = True)

    print("****** All networking2 containers are killed ******")
