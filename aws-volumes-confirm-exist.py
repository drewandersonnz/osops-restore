#!/usr/bin/python
# usage example:
# time ./aws-volumes-stuck.py -v --aws-creds-profile v3-free-prod

import logging
logging.basicConfig(
    format='%(asctime)s - %(relativeCreated)6d - %(levelname)-8s - %(message)s',
)
logger = logging.getLogger()
logger.setLevel(logging.WARN)

import argparse
import boto
import os
import pprint
import random
import time

from openshift_tools.cloud.aws.base import Base

def parse_args():
    """ parse the args from the cli """
    logger.debug("parse_args()")

    parser = argparse.ArgumentParser(description='AWS instance health')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='verbosity level, specify multiple')
    parser.add_argument('--aws-creds-profile', required=False, help='The AWS credentials profile to use.')
    return parser.parse_args()

def getVolumesByRegion(region):
    """ getInstancesByRegion(region) """
    logger.debug("getVolumesByRegion(region): %s", region)
    region = Base(region, verbose=True)
    return region.ec2.get_all_volumes()

def getSnapshotsByRegion(region):
    """ getInstancesByRegion(region) """
    logger.debug("getSnapshotsByRegion(region): %s", region)
    region = Base(region, verbose=True)
    return region.ec2.get_all_snapshots()

def getVolumeId(osid):
    return osid.split('/')[-1]

def getAvailabilityZone(osid):
    return osid.split('/')[-2]

def getSnapshotsByVolumeId(volumeId, snapshots):
    result = []

    for snap in snapshots:
        if snap.volume_id == volumeId:
            result.append(snap)

    return result

def main():
    """ main() """
    logger.debug("main()")

    extra_command = '| jq \'"aws://" + .AvailabilityZone + "/" + .VolumeId\' | tr -d \'"\''

    args = parse_args()

    if args.verbose > 0:
        logger.setLevel(logging.INFO)
    if args.verbose > 1:
        logger.setLevel(logging.DEBUG)

    if args.aws_creds_profile:
        os.environ['AWS_PROFILE'] = args.aws_creds_profile

    region = "us-east-1"

    volumes = getVolumesByRegion(region)
    print "volumes count: %s" % len(volumes)

    volumeids = sorted([v.id for v in volumes])

    requireds = [

        {'name': 'pvc--6673-11e7-b866-', 'id': 'aws://us-east-1c/vol-', },

    ]

    print "requireds count: %s" % len(requireds)

    missings = []

    for required in requireds:
        if getVolumeId(required['id']) not in volumeids:
            missings.append(required)
            print "problem: pvid not in volumeids [%s] [%s]" % (required['name'], required['id'])
        else:
            print "ok: pvid in volumeids [%s] [%s]" % (required['name'], required['id'])

    print "missings count: %s" % len(missings)

    # nothing is missing
    if len(missings) == 0:
        return

    snapshots = getSnapshotsByRegion(region)
    snapshotnames = snapshots[0].volume_id

    for missing in missings:
        snaps = getSnapshotsByVolumeId(getVolumeId(missing['id']), snapshots)

        if len(snaps) == 0:
            print " ".join([
                "# cannot find snapshots for name",
                missing['name'],
                "id",
                missing['id']
            ])
            continue

        random.shuffle(snaps)

        latest_snap = None
        for snap in snaps:
            if not latest_snap:
                latest_snap = snap

            if boto.utils.parse_ts(snap.start_time) > boto.utils.parse_ts(latest_snap.start_time):
                latest_snap = snap

        print " ".join([
            'echo -n %s " "; ' % missing['name'],
            'aws ec2 create-volume',
            '--profile', args.aws_creds_profile,
            '--region', region,
            '--availability-zone', getAvailabilityZone(missing['id']),
            ' --volume-type gp2',
            '--snapshot-id', latest_snap.id,
            '--tag-specifications "ResourceType=volume,Tags=[{Key=Name,Value=kubernetes-dynamic-%s},{Key=kubernetes.io/created-for/pv/name,Value=%s},{Key=restoredate,Value=20171019},{Key=restoresnapid,Value=%s},{Key=old_volumeid,Value=%s}]"' % (missing['name'], missing['name'], latest_snap.id, missing['id']),
            extra_command,
            ';',
        ])

if __name__ == "__main__":
    main()
