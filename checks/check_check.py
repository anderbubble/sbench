#!/usr/bin/env python


import argparse
import random
import sys
import time


RETCODE = {
    'pass': 0,
    'fail': 1,
    'unknown': -1,
}


def main ():
    parser = argparse.ArgumentParser(description='No-op tester with specified or random returncode.')
    retcode_choices = RETCODE.keys() + ['random']
    parser.add_argument('--retcode', choices=retcode_choices, default='random', help='Specify the return code to use (default: random)')
    parser.add_argument('--sleep', type=int, metavar='SECONDS', help='Sleep SECONDS before returning')
    args = parser.parse_args()
    if args.sleep is not None:
        time.sleep(args.sleep)
    if args.retcode == 'random':
        retcode = random.choice(RETCODE.keys())
    else:
        retcode = args.retcode
    print(retcode)
    sys.exit(RETCODE[retcode])


if __name__ == '__main__':
    main()
