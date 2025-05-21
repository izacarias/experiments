#/bin/bash
source .env
export IF_CMD="sudo docker exec -e INFLUX_ORG=$INFLUXDB_ORG -e INFLUX_TOKEN=$INFLUXDB_TOKEN -it influxdb2 influx"

$IF_CMD bucket list

$IF_CMD bucket delete --name dtn05
$IF_CMD bucket delete --name dtn10
$IF_CMD bucket delete --name dtn15
$IF_CMD bucket delete --name dtn20
$IF_CMD bucket delete --name dtn25
$IF_CMD bucket delete --name dtn30
$IF_CMD bucket delete --name dtn35
$IF_CMD bucket delete --name dtn40

$IF_CMD bucket create --name dtn05
$IF_CMD bucket create --name dtn10
$IF_CMD bucket create --name dtn15
$IF_CMD bucket create --name dtn20
$IF_CMD bucket create --name dtn25
$IF_CMD bucket create --name dtn30
$IF_CMD bucket create --name dtn35
$IF_CMD bucket create --name dtn40
