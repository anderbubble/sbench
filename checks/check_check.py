#!/usr/bin/env python


import argparse
import random
import sys
import time


NAGIOS_RETCODE = {
    'ok': 0,
    'warning': 1,
    'critical': 2,
    'unknown': 3,
}


def main ():
    parser = argparse.ArgumentParser()
    retcode_choices = NAGIOS_RETCODE.keys() + ['random']
    parser.add_argument('--retcode', choices=retcode_choices, default='random')
    parser.add_argument('--sleep', type=int)
    args = parser.parse_args()
    if args.sleep is not None:
        time.sleep(args.sleep)
    if args.retcode == 'random':
        retcode = random.choice(NAGIOS_RETCODE.keys())
    else:
        retcode = args.retcode
    print(retcode)
    sys.exit(NAGIOS_RETCODE[retcode])


if __name__ == '__main__':
    main()