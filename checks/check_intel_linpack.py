#!/usr/bin/env python
#
# https://software.intel.com/en-us/mkl-linux-developer-guide-intel-optimized-linpack-benchmark-for-linux


from __future__ import print_function


import argparse
import logging
import re
import subprocess
import sys
import tempfile


PASS = 0
FAIL = 1
UNKNOWN = -1


logger = logging.getLogger('check_intel_hpl')


SUMMARY_P = re.compile(r'^([0-9]+) +([0-9]+) +([0-9]+) +([0-9\.]+) +([0-9\.]+) *$')
RESIDUAL_CHECKS_P = re.compile(r'^Residual checks (.*)$')


HPL_DAT_TEMPLATE = """Intel(R) Optimized LINPACK Benchmark datafile

1 # number of tests
{problem_size} # number of equations (problem sizes)
{leading_dimension} # leading dimensions
{trials} # number of times to run a test (trials)
{alignment} # alignment values (in KBytes)
"""


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('hpl_args', nargs='+')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--problem-size', type=int, default=1000)
    parser.add_argument('--leading-dimension', type=int, default=1000)
    parser.add_argument('--trials', type=int, default=4)
    parser.add_argument('--alignment', type=int, metavar='KBytes', default=4)
    parser.add_argument('--average', type=float)
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = None
    logging.basicConfig(level=log_level)

    hpl_dat = tempfile.NamedTemporaryFile()
    hpl_dat.write(HPL_DAT_TEMPLATE.format(
        problem_size = args.problem_size,
        leading_dimension = args.leading_dimension,
        trials = args.trials,
        alignment = args.alignment,
    ))
    hpl_dat.flush()
    p = hpl(args.hpl_args, dat_file=hpl_dat.name)
    output, _ = p.communicate()
    for line in output.splitlines():
        logger.debug(line.rstrip())
    summary, residual = parse_hpl_output(output)

    if residual is None:
        print('UNKNOWN: no output')
        sys.exit(UNKNOWN)

    average = sum(average for (average, maximal) in summary.itervalues()) / (1.0 * len(summary.values()))

    if residual.lower() != 'passed':
        print('FAIL: Residual checks {0}'.format(residual))
        sys.exit(FAIL)

    if args.average is not None and average < args.average:
        print('FAIL: Average {0} < {1}'.format(average, args.average))
        sys.exit(FAIL)

    print('PASS: Average {0}'.format(average))
    sys.exit(PASS)


def hpl (hpl_args, dat_file=None):
    args = hpl_args[:]
    if dat_file:
        args.extend(('-i', dat_file))
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
