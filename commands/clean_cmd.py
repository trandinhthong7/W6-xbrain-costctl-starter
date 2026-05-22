"""clean — (stretch) bulk terminate resources matching a tag.

WARNING — DESIGN-FOR-SAFETY
---------------------------
This is the most dangerous command in the CLI. Get the contract right:

  1. DEFAULT IS DRY-RUN. Without --apply the command MUST NOT touch resources.
     It only lists what WOULD be deleted.
  2. Even with --apply, you should consider printing a summary count first
     ("about to terminate N EC2 + M volumes — proceed?"), though for this
     starter a hard `--apply` flag is enough.
  3. Never use this with a tag you don't fully own. Reflection prompt in
     README covers the blast-radius scenario.

WHAT YOU MUST BUILD
-------------------
1. `_find_targets(tag_key, tag_val)` — return a dict like:
     {"ec2": [<instance ids in non-terminal state>],
      "volume": [<volume ids in 'available' state only>]}
   Skip terminated/shutting-down instances (already gone).
   Skip in-use volumes (can't delete while attached — would error anyway).

2. `run(args)` — call _find_targets, print the plan, then either:
     - bail with "(dry-run — pass --apply to ...)"  (default)
     - or actually terminate (when --apply)

HELPERS YOU CAN USE
-------------------
From commands._common:
  parse_kv(s) -> (k, v)

AWS APIS YOU'LL NEED
--------------------
- ec2.describe_instances() + describe_volumes() — same as list_cmd
- ec2.terminate_instances(InstanceIds=[...])
- ec2.delete_volume(VolumeId=...)  (per volume, no bulk API)

VERIFY
------
    pytest tests/test_clean.py -v
"""
import boto3

from commands._common import parse_kv


def _find_targets(tag_key, tag_val):
    """Return {"ec2": [...], "volume": [...]} matching tag in non-terminal state."""
    ec2 = boto3.client("ec2")
    
    # EC2 instances
    paginator_ec2 = ec2.get_paginator('describe_instances')
    ec2_targets = []
    for page in paginator_ec2.paginate():
        for res in page.get('Reservations', []):
            for inst in res.get('Instances', []):
                state = inst['State']['Name']
                if state in ('shutting-down', 'terminated'):
                    continue
                
                tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                if tags.get(tag_key) == tag_val:
                    ec2_targets.append(inst['InstanceId'])

    # EBS volumes
    paginator_vol = ec2.get_paginator('describe_volumes')
    vol_targets = []
    for page in paginator_vol.paginate():
        for vol in page.get('Volumes', []):
            if vol['State'] != 'available':
                continue
                
            tags = {t["Key"]: t["Value"] for t in vol.get("Tags", [])}
            if tags.get(tag_key) == tag_val:
                vol_targets.append(vol['VolumeId'])
                
    return {"ec2": ec2_targets, "volume": vol_targets}


def run(args):
    """Entry point.

    Args set by argparse:
        args.tag    — "key=value" string (REQUIRED)
        args.apply  — bool, must be True to actually delete (default False = dry-run)
    """
    k, v = parse_kv(args.tag)
    targets = _find_targets(k, v)
    
    count_ec2 = len(targets["ec2"])
    count_vol = len(targets["volume"])
    
    if count_ec2 == 0 and count_vol == 0:
        print("Nothing to clean.")
        return
        
    print(f"Found {count_ec2} EC2 instances and {count_vol} EBS volumes matching {args.tag}.")
    
    if not args.apply:
        print("(dry-run — pass --apply to actually terminate)")
        return
        
    ec2 = boto3.client("ec2")
    if targets["ec2"]:
        ec2.terminate_instances(InstanceIds=targets["ec2"])
        print(f"Terminated {count_ec2} EC2 instances.")
        
    for vol_id in targets["volume"]:
        ec2.delete_volume(VolumeId=vol_id)
        
    if count_vol:
        print(f"Deleted {count_vol} EBS volumes.")
