#!/usr/bin/env python

# https://www.netlib.org/benchmark/hpl/software.html
# https://www.netlib.org/benchmark/hpl/tuning.html


from __future__ import print_function


import argparse
import json
import re
import subprocess
import sys


NAGIOS_OK = 0
NAGIOS_WARNING = 1
NAGIOS_CRITICAL = 2
NAGIOS_UNKNOWN = 3


SUMMARY_P = re.compile(r'^([0-9]+) +([0-9]+) +([0-9]+) +([0-9\.]+) +([0-9\.]+)$')
RESIDUAL_CHECKS_P = re.compile(r'^Residual checks (.*)$')


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('hpl_args', nargs='+')
    parser.add_argument('--warning-average', type=float)
    parser.add_argument('--critical-average', type=float)
    args = parser.parse_args()

    p = hpl(args.hpl_args)
    output, _ = p.communicate()
    summary, residual = parse_hpl_output(output)

    if not output and residual is None:
        print('UNKNOWN: no output')
        sys.exit(NAGIOS_UNKNOWN)

    average = sum(average for (average, maximal) in summary.itervalues()) / (1.0 * len(summary.values()))

    if residual.lower() != 'passed':
        print('CRITICAL: Residual checks {0}'.format(residual))
        sys.exit(NAGIOS_CRITICAL)

    if args.critical_average is not None and average < args.critical_average:
        print('CRITICAL: Average {0} < {1}'.format(average, args.critical_average))
        sys.exit(NAGIOS_CRITICAL)

    if args.warning_average is not None and average < args.warning_average:
        print('WARNING: Average {0} < {1}'.format(average, args.warning_average))
        sys.exit(NAGIOS_CRITICAL)

    print('OK: Average {0}'.format(average))
    sys.exit(NAGIOS_OK)


def hpl (hpl_args):
    args = hpl_args[:]
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    return p


def parse_hpl_output (output):
    summary = {}
    section = None
    residual = None
    for line in output.splitlines():
        if line == 'Performance Summary (GFlops)':
            section = 'summary'
            continue
        elif line.startswith('Residual checks'):
            section = None
            m = RESIDUAL_CHECKS_P.match(line)
            if m:
                residual = m.group(1)
        elif section == 'summary':
            m = SUMMARY_P.match(line)
            if m:
                size, lda, align, average, maximal = m.groups()
                summary[(int(size), int(lda), int(align))] = (float(average), float(maximal))
    return summary, residual

if __name__ == '__main__':
    main()
