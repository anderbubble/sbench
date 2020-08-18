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
    parser = argparse.ArgumentParser()
    retcode_choices = RETCODE.keys() + ['random']
    parser.add_argument('--retcode', choices=retcode_choices, default='random')
    parser.add_argument('--sleep', type=int)
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
