
#!/bin/bash

# export IP_ADDR=$(awk 'END{print $1}' /etc/hosts)

sleep 35
./nr-ue -c /mnt/ueransim/ue.yaml > /mnt/log/ue.log 2>&1
