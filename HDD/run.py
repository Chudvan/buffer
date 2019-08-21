import os
import sys
import time


TIME_SLEEP = 5 * 60
DELETE_UNTIL = 2592000


def check_args():
    if len(sys.argv) != 1:
        raise TypeError("""Error: Too many arguments.
            Usage: python run.py""")


def parse_disk_list():
    list_disks = os.popen('fdisk -l | grep \ /dev/').read()
    if not list_disks:
        print('Warning: empty list_disks.')
        print('Continue? (y/n)')
        answer = input()[0]
        if answer != 'y':
            sys.exit(-1)
    return [string.split()[-1] for string in list_disks.split(':')[:-1]]


def run_smartctl(list_disks, TIME_SLEEP):
    for disk in list_disks:
        os.popen('smartctl -t short "{}"'.format(disk))
        time.sleep(TIME_SLEEP)


def delete_entries(DELETE_UNTIL):
    os.system('python "{}" "{}"'.format('delete_entry.py', time.time() - DELETE_UNTIL))


def new_tests():
    for disk in list_disks:
        os.system('python "{}" "{}"'.format('HDD.py', disk))


check_args()
list_disks = parse_disk_list()
run_smartctl(list_disks, TIME_SLEEP)
delete_entries(DELETE_UNTIL)
new_tests()
