#!/usr/bin/env python

from __future__ import print_function

import argparse
import re
import subprocess
import hostlist
import logging


NODE_NAME_P = re.compile(r'^NodeName=([^ ]+)')
NODES_P = re.compile(r' Nodes=([^ \n]+)')


def main ():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--partition')
    args = parser.parse_args()

    nodes = set(get_all_nodes())
    logging.debug('all nodes: {0}'.format(len(nodes)))
    if args.partition:
        nodes = nodes & set(get_partition_nodes(args.partition))
        logging.debug('partition nodes: {0}'.format(len(nodes)))


def get_all_nodes ():
    p = scontrol('show nodes')
    for line in p.stdout:
        for match in NODE_NAME_P.finditer(line):
            yield match.group(1)
    p.wait()


def get_partition_nodes (partition):
    p = scontrol('show partition {0}'.format(partition))
    for line in p.stdout:
        for match in NODES_P.finditer(line):
            for node in hostlist.expand_hostlist(match.group(1)):
                yield node
    p.wait()


def srun (_exe='/usr/bin/srun'):
    args = [_exe]
    p = subprocess.Popen(args)
    p.communicate()


def scontrol (command, _exe='/usr/bin/scontrol'):
    args = [_exe]
    args.extend(command.split())
    return subprocess.Popen(args, stdout=subprocess.PIPE)


if __name__ == '__main__':
    main()
