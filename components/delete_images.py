import os, sys
import docker
from remove_containers import *



client = docker.from_env()
images = client.images

remove_containers()

for image in images.list():
    if("networking2" in str(image)):
        client.images.remove(str(image.tags[0]))
        

print("****** All networking2 images are removed ******")