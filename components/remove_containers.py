import os, sys
import docker

def remove_containers():
    client = docker.from_env()
    containers = client.containers
    for container in containers.list():
        # remove also exited and networks...
        if("dev_test" in str(container.image) or "mysql" in str(container.image) or "oaisoftwarealliance" in str(container.image)):
            container.remove(force = True)

    print("****** All project containers have been killed ******")
