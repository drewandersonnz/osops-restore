* confirm PVs which need restore

oc get pv -o go-template='{{range .items}}{{.metadata.name}}{{print " "}}{{.spec.awsElasticBlockStore.volumeID}}{{ println }}{{end}}'

oc get pv -o json | jq '.items[] | .metadata.name + " " + .spec.awsElasticBlockStore.volumeID


* check for snapshots for each pv
* recreate new EBS Volume, with name, from snapshots
* edit PV definitions to point to new EBS volume
