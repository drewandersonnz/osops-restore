* confirm PVs which need restore
```
oc get pv -o go-template='{{range .items}}{{.metadata.name}}{{print " "}}{{.spec.awsElasticBlockStore.volumeID}}{{ println }}{{end}}'
```
```
oc get pv -o json | jq '.items[] | .metadata.name + " " + .spec.awsElasticBlockStore.volumeID
```
* check for snapshots for each pv
* recreate new EBS Volume, with name, from snapshots
```
aws ec2 create-volume --region us-east-1 --availability-zone us-east-1a --volume-type gp2 --snapshot-id snap-066877671789bd71b
{
    "AvailabilityZone": "us-east-1a",
    "Attachments": [],
    "Tags": [],
    "VolumeType": "gp2",
    "VolumeId": "vol-1234567890abcdef0",
    "State": "creating",
    "SnapshotId": null,
    "CreateTime": "YYYY-MM-DDTHH:MM:SS.000Z",
    "Size": 80
}

should be able to pipe through:
jq '"aws://" + .AvailabilityZone + "/" + .VolumeId' | tr -d '"'

to get:
aws://us-east-1a/vol-1234567890abcdef0
```
* edit PV definitions to point to new EBS volume
```
oc patch pv pvc-422c7fa0-b519-11e7-92e8-0a46c474dfe0 --type=json -p '[{"op":"replace", "path": "/spec/awsElasticBlockStore/volumeID", "value": "aws://us-east-1c/vol-03fa29c13d6330de3" }]'
```
see: (update-pv-volume.sh)
