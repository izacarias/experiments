# System
> [!note]
> **Lubuntu** 22.04.5 LTS
## Upgrade the system
```
sudo apt update && sudo apt upgrade -y
```
## Install Mininet
```
git clone https://github.com/mininet/mininet
mininet/util/install.sh -nfv
```
## Test Mininet
```bash
sudo mn --switch ovsbr --test pingall
```
## Install Docker and Docker Compose
```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo apt-get install -y docker-compose
sudo usermod -aG docker $USER
```

## Install `hsflowd`
```bash
cd ~/Downloads
wget -c https://github.com/sflow/host-sflow/releases/download/v2.0.53-1/hsflowd-ubuntu22_2.0.53-1_amd64.deb
sudo dpkg -i hsflowd-ubuntu22_2.0.53-1_amd64.deb
```

## Install influxdb-client
```bash
sudo pip install influxdb-client
sudo pip install python-dotenv
```
# Running the experiments
## Start all docker images
```bash
docker-compose up -d
```
### Access ONOS
```
http://localhost:8181/onos/ui

user: onos
password: rocks
``` 
### Make sure the following applications are running on ONOS
``` 
org.onosproject.drivers
org.onosproject.hostprovider
org.onosproject.lldpprovider
org.onosproject.gui2
org.onosproject.openflow-base
org.onosproject.openflow
org.onosproject.optical-model
org.onosproject.proxyarp
org.onosproject.fwd
```
### Access sflow-ft
```
http://localhost:8008
```

### Mininet sample script
Check the file `network1.py`
