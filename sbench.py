#!/usr/bin/env python

from __future__ import print_function

import argparse
import psutil
import re
import subprocess
import hostlist
import logging
import time


NODE_NAME_P = re.compile(r'^NodeName=([^ ]+)')
STATE_P = re.compile(r'State=([^ ]+)')
NODES_P = re.compile(r' Nodes=([^ \n]+)')

POLLING_INTERVAL=2

NAGIOS_OK = 0
NAGIOS_WARNING = 1
NAGIOS_CRITICAL = 2
NAGIOS_UNKNOWN = 3


logger = logging.getLogger('sbench')


def main ():
    parser = argparse.ArgumentParser(description='Launch groups of test scripts with srun.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging (default: info)')
    parser.add_argument('--partition', help='Specify a partition for node selection and job submission')
    parser.add_argument('--mpi', help='Enable MPI support for srun')
    parser.add_argument('--ntasks', help='Specify the number of tasks to run for each job')
    parser.add_argument('--ntasks-per-node', help='Specify the number of tasks to run on each node for each job')
    parser.add_argument('--state', action='append', help='Specify valid node states for node selection')
    parser.add_argument('--account', help='Specify the account to use during srun')
    parser.add_argument('--chdir', help='Specify a directory to use for srun')
    parser.add_argument('--time', help='Specify a job runtime to use for srun')
    parser.add_argument('--nodelist', help='Specify a node list to use for node selection')
    parser.add_argument('--nodes', type=int, help='Specify the number of nodes to use for srun')
    parser.add_argument('--bcast', nargs='?', const=True, help='Copy executable file to compute nodes during srun')
    parser.add_argument('--exclusive', action='store_true', help='Exclusive use of compute nodes during srun')
    parser.add_argument('--timeout', type=int, help='Terminate jobs after a timeout (seconds)')
    parser.add_argument('executable', help='Executable to execute')
    parser.add_argument('executable_arguments', nargs='*', help='Arguments for the test executable')
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)

    all_nodes = set(get_all_nodes(states=args.state))
    if args.partition:
        all_nodes = all_nodes & set(get_partition_nodes(args.partition))
    if args.nodelist:
        all_nodes = all_nodes & set(hostlist.expand_hostlist(args.nodelist))
    all_nodes = list(sorted(all_nodes))

    jobs = [(nodelist, srun(args.executable, args.executable_arguments,
                           partition=args.partition,
                           nodelist=','.join(nodelist), ntasks=args.ntasks,
                           account=args.account, chdir=args.chdir,
                           time=args.time, bcast=args.bcast,
                           exclusive=args.exclusive, nodes=args.nodes,
                           ntasks_per_node=args.ntasks_per_node, mpi=args.mpi))
            for nodelist in split_nodes(all_nodes, args.nodes)]

    start_time = time.time()
    completed_jobs = set()
    new_completed_jobs = []
    ok = set()
    warning = set()
    critical = set()
    unknown = set()
    while True:
        for nodelist, job in jobs:
            job.poll()
            if job.returncode is not None and job not in completed_jobs:
                new_completed_jobs.append((nodelist, job))
                if job.returncode == NAGIOS_OK:
                    ok |= set(nodelist)
                elif job.returncode == NAGIOS_WARNING:
                    warning |= set(nodelist)
                elif job.returncode == NAGIOS_CRITICAL:
                    critical |= set(nodelist)
                else:
                    unknown |= set(nodelist)
            elif args.timeout is not None and (time.time() - start_time > args.timeout):
                logger.warning('{0}: {1}'.format(','.join(nodelist), 'timeout'))
                job.terminate()
        if new_completed_jobs:
            for nodelist, job in new_completed_jobs:
                for line in job.stderr:
                    logger.debug('{0}: {1}'.format(','.join(nodelist), line.rstrip()))
                for line in job.stdout:
                    logger.info('{0}: {1}'.format(','.join(nodelist), line.rstrip()))
                    break
                completed_jobs.add(job)
            new_completed_jobs = []
        if completed_jobs == set(job for _, job in jobs):
            break
        else:
            time.sleep(POLLING_INTERVAL)
            continue

    if ok:
        print('ok:', hostlist.collect_hostlist(ok))
    if warning:
        print('warning:', hostlist.collect_hostlist(warning))
    if critical:
        print('critical:', hostlist.collect_hostlist(critical))
    if unknown:
        print('unknown:', hostlist.collect_hostlist(unknown))


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


def split_nodes (all_nodes, nodes_per_set):
    for i in range(0, len(all_nodes), nodes_per_set):  
        yield all_nodes[i:i + nodes_per_set]


def srun (executable, executable_arguments, partition=None,
          nodelist=None, ntasks=None, account=None, chdir=None,
          time=None, bcast=None, exclusive=None, nodes=None, mpi=None,
          ntasks_per_node=None, srun_='/usr/bin/srun'):
    args = [srun_]
    if partition is not None:
        args.append('--partition={0}'.format(partition))
    if nodelist is not None:
        args.append('--nodelist={0}'.format(nodelist))
    if nodes is not None:
        args.append('--nodes={0}'.format(nodes))
    if ntasks is not None:
        args.append('--ntasks={0}'.format(ntasks))
    if account is not None:
        args.append('--account={0}'.format(account))
    if chdir is not None:
        args.append('--chdir={0}'.format(chdir))
    if time is not None:
        args.append('--time={0}'.format(time))
    if bcast is True:
        args.append('--bcast')
    elif bcast is not None:
        args.append('--bcast={0}'.format(bcast))
    if exclusive:
        args.append('--exclusive')
    if ntasks_per_node is not None:
        args.append('--ntasks-per-node={0}'.format(ntasks_per_node))
    if mpi is not None:
        args.append('--mpi={0}'.format(mpi))
    args.append(executable)
    args.extend(executable_arguments)
    logger.debug(' '.join(args))
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def scontrol (command, scontrol_='/usr/bin/scontrol'):
    args = [scontrol_, '--oneliner']
    args.extend(command.split())
    return subprocess.Popen(args, stdout=subprocess.PIPE)


if __name__ == '__main__':
    main()
