import os, sys
import docker


client = docker.from_env()
images = client.images
containers = client.containers

for container in containers.list():
    if("networking2" in str(container.image)):
        container.kill()

print("****** All networking2 containers are killed ******")

for image in images.list():
    if("networking2" in str(image)):
        client.images.remove(str(image.tags[0]))
        

print("****** All networking2 images are removed ******")