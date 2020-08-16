#!/usr/bin/env python

from __future__ import print_function


import argparse
import collections
import logging
import os
import re
import subprocess
import sys


HEADER_P = re.compile(r'^ *# *Size *Bandwidth \((.*)\) *$', flags=re.MULTILINE)
RESULTS_P = re.compile(r'^ *([0-9]+) *([0-9\.]+) *$', flags=re.MULTILINE)


NAGIOS_OK = 0
NAGIOS_WARNING = 1
NAGIOS_CRITICAL = 2
NAGIOS_UNKNOWN = 3


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--test', dest='tests', action='append', type=test_spec, default=[])
    parser.add_argument('osu_bibw_args', nargs='+')
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = None
    logging.basicConfig(level=log_level)

    p = subprocess.Popen(args.osu_bibw_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = p.communicate()

    mpi_rank = get_mpi_rank()
    logging.debug('mpi rank: {mpi_rank}'.format(mpi_rank=mpi_rank))
    if mpi_rank is not None and mpi_rank != 0:
        sys.exit()

    for match in HEADER_P.finditer(output):
        bandwidth_scale = match.group(1)
        break
    else:
        bandwidth_scale = '?/s'

    results = collections.defaultdict(list)
    for match in RESULTS_P.finditer(output):
        size, bandwidth = match.groups()
        results[int(size)].append(float(bandwidth))

    averages = {size: mean(bandwidths) for (size, bandwidths) in results.iteritems()}

    best_size = None
    for size, average_bandwidth in averages.iteritems():
        if best_size is None or average_bandwidth > averages[best_size]:
            best_size = size

    for test_size, test_bandwidth in args.tests:
        if test_size is not None:
            try:
                bandwidth = averages[test_size]
            except KeyError:
                logging.warning('size {size} not tested'.format(size=test_size))
                continue
        else:
            bandwidth = averages[best_size]

        if bandwidth < test_bandwidth:
            print('CRITICAL: size={size} bandwidth {bandwidth} < {test_bandwidth} ({bandwidth_scale})'.format(
                size=test_size if test_size is not None else best_size,
                bandwidth=bandwidth,
                test_bandwidth=test_bandwidth,
                bandwidth_scale=bandwidth_scale,
            ))
            sys.exit(NAGIOS_CRITICAL)

    if not averages:
        print('UNKNOWN: no test results')
        sys.exit(NAGIOS_UNKNOWN)

    print('OK: size={size} bandwidth={bandwidth} ({bandwidth_scale})'.format(
        size=best_size,
        bandwidth=averages[best_size],
        bandwidth_scale=bandwidth_scale,
    ))
    sys.exit(NAGIOS_OK)


def mean (values):
    return 1.0 * sum(values) / len(values)


def test_spec (spec_str):
    if ',' in spec_str:
        size, bandwidth = spec_str.split(',', 1)
    else:
        size = None
        bandwidth = spec_str
    return int(size) if size is not None else size, float(bandwidth)


def get_mpi_rank ():
    if 'SLURM_PROCID' in os.environ:
        return int(os.environ['SLURM_PROCID'])

    for key, value in os.environ.iteritems():
        if key.endswith('_RANK'):
            try:
                return int(value)
            except ValueError:
                continue


if __name__ == '__main__':
    main()
