import os, sys
import docker


client = docker.from_env()
containers = client.containers

for container in containers.list():
    if("networking2" in str(container.image)):
        container.kill()

print("****** All networking2 containers are killed ******")
