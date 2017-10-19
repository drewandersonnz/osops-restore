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
import os
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
    logger.debug("getInstanceStatusesByRegion(region): %s", region)
    region = Base(region, verbose=True)
    return region.ec2.get_all_volumes()

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

    volumeids = sorted([v.id for v in volumes])

    print "\n".join(volumeids)

    ospv = "pvc-02744467-94ca-11e7-b0cb-12b5519f9b58"
    osid = "aws://us-east-1c/vol-04f527a64d902913a"

    if getVolumeId(osid) not in volumeids:
        print "problem: pvid not in volumeids [%s] [%s]" % (ospv, osid)



    #for volume in volumes:
    #    testVolume(volume, region=region, args=args, )

if __name__ == "__main__":
    main()
