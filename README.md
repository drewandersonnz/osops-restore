* confirm PVs which need restore
```
oc get pv -o go-template='{{range .items}}{{.metadata.name}}{{print " "}}{{.spec.awsElasticBlockStore.volumeID}}{{ println }}{{end}}'
```
```
oc get pv -o json | jq '.items[] | .metadata.name + " " + .spec.awsElasticBlockStore.volumeID
```
* check for snapshots for each pv
* recreate new EBS Volume, with name, from snapshots
* edit PV definitions to point to new EBS volume
```
oc patch pv pvc-422c7fa0-b519-11e7-92e8-0a46c474dfe0 --type=json -p '[{"op":"replace", "path": "/spec/awsElasticBlockStore/volumeID", "value": "aws://us-east-1c/vol-03fa29c13d6330de3" }]'
```
