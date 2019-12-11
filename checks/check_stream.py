#!/usr/bin/env python
#
# https://www.cs.virginia.edu/stream/


from __future__ import print_function


import argparse
import logging
import re
import subprocess
import sys


RESULTS_P = re.compile(r'^(Copy|Scale|Add|Triad): +([0-9\.]+) +([0-9\.]+) +([0-9\.]+) +([0-9\.]+)$', flags=re.MULTILINE)
VALIDATION_P = re.compile(r'Solution Validates')

NAGIOS_OK = 0
NAGIOS_WARNING = 1
NAGIOS_CRITICAL = 2
NAGIOS_UNKNOWN = 3

THRESHOLDS = ('warning', 'critical')
CMD_FUNCTIONS = ('copy', 'scale', 'add', 'triad')
ARG_FUNCTIONS = CMD_FUNCTIONS
RESULT_FUNCTIONS = [function.capitalize() for function in ARG_FUNCTIONS]
CMD_FACTORS = ('rate', 'avg-time', 'min-time', 'max-time')
ARG_FACTORS = ('rate', 'avg_time', 'min_time', 'max_time')


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('stream_args', nargs='+')
    for function in CMD_FUNCTIONS:
        for factor in CMD_FACTORS:
            for threshold in THRESHOLDS:
                if factor == 'rate':
                    metavar = 'MB/s'
                else:
                    metavar = 'SECONDS'
                parser.add_argument('--{0}-{1}-{2}'.format(function, factor, threshold), type=float, metavar=metavar)
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = None
    logging.basicConfig(level=log_level)

    p = subprocess.Popen(args.stream_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = p.communicate()
    results = {}
    for match in RESULTS_P.finditer(output):
        function, rate, avg_time, min_time, max_time = match.groups()
        assert function not in results
        results[function] = (float(rate), float(avg_time), float(min_time), float(max_time))
    logging.debug(results)

    validation = VALIDATION_P.search(output)
    if validation is None:
        print('CRITICAL: Solution does not validate')
        sys.exit(NAGIOS_CRITICAL)

    for threshold in THRESHOLDS:
        for arg_function, result_function in zip(ARG_FUNCTIONS, RESULT_FUNCTIONS):
            for factor in ARG_FACTORS:
                threshold_value = getattr(args, '{0}_{1}_{2}'.format(arg_function, factor, threshold))
                if threshold_value is None:
                    continue
                result_value = get_value(results, result_function, factor)
                if factor == 'rate' and result_value < threshold_value:
                    print('{0}: {1} {2} {3} < {4}'.format(threshold.upper(), result_function, factor, result_value, threshold_value))
                    exit_from_threshold(threshold)

                elif result_value > threshold_value:
                    print('{0}: {1} {2} {3} > {4}'.format(threshold.upper(), result_function, factor, result_value, threshold_value))
                    exit_from_threshold(threshold)

    print('OK: {0}'.format(validation.group(0)))
    sys.exit(NAGIOS_OK)


def exit_from_threshold (threshold):
    if threshold == 'critical':
        sys.exit(NAGIOS_CRITICAL)
    elif threshold == 'warning':
        sys.exit(NAGIOS_WARNING)
    else:
        sys.exit(NAGIOS_UNKNOWN)


def get_value (results, function, factor):
    factor_i = ARG_FACTORS.index(factor)
    return results[function][factor_i]
                                

if __name__ == '__main__':
    main()
