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
    #parser.add_argument('--id', required=False, help='id.')
    #parser.add_argument('--name', required=False, help='name.')
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

def testVolume(volume, region="", args={}, ):

    #if not volume.attachment_state() in ['attaching']:
    if not volume.attachment_state() in ['attaching', 'busy', ]:
        return

    print '# ' + ' '.join([
        volume.attachment_state(),
        volume.id,
        volume.zone,
        volume.attach_data.instance_id,
    ])

    print '# aws ' + ' '.join([
        'ec2 stop-instances --force',
        '--profile', args.aws_creds_profile,
        '--region', region,
        '--instance-ids', volume.attach_data.instance_id,
    ])

    print '# aws ' + ' '.join([
        'ec2 start-instances',
        '--profile', args.aws_creds_profile,
        '--region', region,
        '--instance-ids', volume.attach_data.instance_id,
    ])

def getVolumeId(osid):
    return osid.split('/')[-1]

def getAvailabilityZone(osid):
    return osid.split('/')[-2]

def getSnapshotsByVolumeId(volumeId, snapshots):
    result = []

    for snap in snapshots:
        if snap.volume_id == volumeId:
            result.append(snap)

    #result.sort(cmp=lambda x,y: cmp(x.date, y.date))
    return result

def main():
    """ main() """
    logger.debug("main()")

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

    print "\n".join(volumeids)

#    requireds = [
#        {'name': 'pvc-024940fb-7e2d-11e7-9104-125b034d2f46', 'id': 'aws://us-east-1c/vol-036d1dd4491d03523', },
#        {'name': 'pvc-0250be99-90d9-11e7-8584-123713f594ec', 'id': 'aws://us-east-1c/vol-0c2e7342add799bb0', },
#        {'name': 'pvc-02744467-94ca-11e7-b0cb-12b5519f9b58', 'id': 'aws://us-east-1c/vol-04f527a64d902913a', },
#    ]
#
    requireds = [
        {'name': 'pvc-fc1c5be5-a785-11e7-82f8-0a46c474dfe0', 'id': 'aws://us-east-1c/vol-0a78dfd8f7cec4650', },
        {'name': 'pvc-422c7fa0-b519-11e7-92e8-0a46c474dfe0', 'id': 'aws://us-east-1c/vol-03fa29c13d6330de2', },
    ]

    print "requireds count: %s" % len(requireds)

    missings = []

    for required in requireds:
        if getVolumeId(required['id']) not in volumeids:
            missings.append(required)
            print "problem: pvid not in volumeids [%s] [%s]" % (required['name'], required['id'])

    print missings
    print "missings count: %s" % len(missings)

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
            'aws ec2 create-volume',
            '--profile', args.aws_creds_profile,
            '--region', region,
            '--availability-zone', getAvailabilityZone(missing['id']),
            ' --volume-type gp2',
            '--snapshot-id', latest_snap.id,
            '--tag-specifications "ResourceType=volume,Tags=[{Key=name,Value=kubernetes-dynamic-%s},{Key=restoredate,Value=20171019},{Key=restoresnapid,Value=%s},{Key=old_volumeid,Value=%s}]"' % (missing['name'], latest_snap.id, missing['id']),
            ';',
        ])

#aws ec2 create-volume --region us-east-1 --availability-zone us-east-1c  --volume-type gp2 --snapshot-id snap-0549c90cb17848fd1 --tag-specifications "ResourceType=string,Tags=[{Key=name,Value=kubernetes-dynamic-pvc-024940fb-7e2d-11e7-9104-125b034d2f46},{Key=restoredate,Value=20171019},{Key=restoresnapid,Value=snap-0549c90cb17848fd1},{Key=old_volumeid,Value=aws://us-east-1c/vol-036d1dd4491d03523}]"
#aws ec2 create-volume --region us-east-1 --availability-zone us-east-1c  --volume-type gp2 --snapshot-id snap-09ada71e8650e3560 --tag-specifications "ResourceType=string,Tags=[{Key=name,Value=kubernetes-dynamic-pvc-0250be99-90d9-11e7-8584-123713f594ec},{Key=restoredate,Value=20171019},{Key=restoresnapid,Value=snap-09ada71e8650e3560},{Key=old_volumeid,Value=aws://us-east-1c/vol-0c2e7342add799bb0}]"
#aws ec2 create-volume --region us-east-1 --availability-zone us-east-1c  --volume-type gp2 --snapshot-id snap-0dcac434b75e74f7f --tag-specifications "ResourceType=string,Tags=[{Key=name,Value=kubernetes-dynamic-pvc-02744467-94ca-11e7-b0cb-12b5519f9b58},{Key=restoredate,Value=20171019},{Key=restoresnapid,Value=snap-0dcac434b75e74f7f},{Key=old_volumeid,Value=aws://us-east-1c/vol-04f527a64d902913a}]"
#

if __name__ == "__main__":
    main()
