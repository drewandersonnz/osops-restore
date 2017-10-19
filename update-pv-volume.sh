#!/bin/bash

set -e

if [ "$#" -ne 2 ]; then
  echo "Illegal number of parameters, must be PV name, EBS volume id"
  exit 1
fi
pv="$1"
vol="$2"

prev=$(oc get pv "${pv}" -o json | jq '.spec.awsElasticBlockStore.volumeID' | tr -d '"')
echo patching "${pv}" from: "${prev}" to "${vol}"

patch="[{\"op\":\"replace\", \"path\": \"/spec/awsElasticBlockStore/volumeID\", \"value\": \"${vol}\" }]"
oc patch pv "${pv}" --type=json -p "${patch}"

