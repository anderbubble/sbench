#!/usr/bin/env python

from __future__ import print_function

import argparse
import re
import subprocess
import hostlist
import logging
import time


NODE_NAME_P = re.compile(r'^NodeName=([^ ]+)')
STATE_P = re.compile(r'State=([^ ]+)')
NODES_P = re.compile(r' Nodes=([^ \n]+)')

POLLING_INTERVAL=2


def main ():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--partition')
    parser.add_argument('--ntasks')
    parser.add_argument('--state', action='append')
    parser.add_argument('--account')
    parser.add_argument('--chdir')
    parser.add_argument('--time')
    parser.add_argument('--bcast', nargs='?', const=True)
    parser.add_argument('executable')
    parser.add_argument('executable_arguments', nargs='*')
    args = parser.parse_args()

    nodes = set(get_all_nodes(states=args.state))
    if args.partition:
        nodes = nodes & set(get_partition_nodes(args.partition))
    nodes = list(sorted(nodes))
    logging.debug('nodes: {0}'.format(len(nodes)))

    jobs = [srun(args.executable, args.executable_arguments,
                 partition=args.partition, nodelist=node,
                 ntasks=args.ntasks, account=args.account,
                 chdir=args.chdir, time=args.time, bcast=args.bcast)
            for node in nodes]

    completed_jobs = set()
    new_completed_jobs = set()
    while True:
        for node, job in zip(nodes, jobs):
            job.poll()
            if job.returncode is not None and job not in completed_jobs:
                new_completed_jobs.add(job)
                print(job.returncode, node, job.stdout.read().strip())
        if new_completed_jobs:
            completed_jobs |= new_completed_jobs
            new_completed_jobs = set()
            logging.debug('completed: {0}/{1}'.format(len(completed_jobs), len(jobs)))
        if completed_jobs == set(jobs):
            break
        else:
            time.sleep(POLLING_INTERVAL)
            continue


def get_all_nodes (states=None):
    p = scontrol('show nodes')
    for line in p.stdout:
        if states is not None:
            if STATE_P.search(line).group(1).lower() not in [state.lower() for state in states]:
                continue
            else:
                yield NODE_NAME_P.search(line).group(1)
    p.wait()


def get_partition_nodes (partition):
    p = scontrol('show partition {0}'.format(partition))
    for line in p.stdout:
        for match in NODES_P.finditer(line):
            for node in hostlist.expand_hostlist(match.group(1)):
                yield node
    p.wait()


def srun (executable, executable_arguments, partition=None, nodelist=None, ntasks=None,
          account=None, chdir=None, time=None, bcast=None, srun_='/usr/bin/srun'):
    args = [srun_]
    if partition:
        args.extend(('--partition', partition))
    if nodelist:
        args.extend(('--nodelist', nodelist))
    if ntasks:
        args.extend(('--ntasks', ntasks))
    if account:
        args.extend(('--account', account))
    if chdir:
        args.extend(('--chdir', chdir))
    if time:
        args.extend(('--time', time))
    if bcast is True:
        args.append('--bcast')
    elif bcast:
        args.append('--bcast={0}'.format(bcast))
    args.append(executable)
    return subprocess.Popen(args, stdout=subprocess.PIPE)


def scontrol (command, scontrol_='/usr/bin/scontrol'):
    args = [scontrol_, '--oneliner']
    args.extend(command.split())
    return subprocess.Popen(args, stdout=subprocess.PIPE)


if __name__ == '__main__':
    main()
